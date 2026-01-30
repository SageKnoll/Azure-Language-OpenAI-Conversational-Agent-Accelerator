# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# Modified for IRIS Symphony OSHA by Sagevia
"""
IRIS Symphony OSHA - Semantic Kernel Orchestrator
==================================================
Multi-agent orchestration using Azure AI Foundry agents with
Semantic Kernel GroupChat for OSHA recordkeeping assistance.

Agent Architecture:
  TranslationAgent → TriageAgent → Lumi → SAGE Agents
                                           ├─ SciencesAgent (📚)
                                           ├─ GovernanceAgent (⚖️)
                                           ├─ AnalyticsAgent (📊)
                                           └─ ExperienceAgent (🤝)
"""

import os
import json
import asyncio
from typing import Callable
from semantic_kernel.agents import AzureAIAgent, GroupChatOrchestration, GroupChatManager, BooleanResult, StringResult, MessageResult
from semantic_kernel.contents import ChatMessageContent, ChatHistory, AuthorRole
from semantic_kernel.agents.runtime import InProcessRuntime
from azure.ai.projects import AIProjectClient
from pydantic import BaseModel

# IRIS Symphony OSHA Plugins (IRI Domain Agents)
from agents.sciences_plugin import SciencesPlugin
from agents.regulatory_guidance_plugin import RegulatoryGuidancePlugin
from agents.recordability_plugin import RecordabilityPlugin
from agents.industry_analytics_plugin import IndustryAnalyticsPlugin
from agents.incident_management_plugin import IncidentManagementPlugin
from agents.document_generation_plugin import DocumentGenerationPlugin

# Define confidence thresholds
confidence_threshold = float(os.environ.get("CLU_CONFIDENCE_THRESHOLD", "0.7"))
cqa_confidence = float(os.environ.get("CQA_CONFIDENCE", "0.8"))


class ChatMessage(BaseModel):
    role: str
    content: str


# =============================================================================
# ROUTING FUNCTIONS - Handle message flow between agents
# =============================================================================

def route_user_message(participant_descriptions: dict) -> StringResult:
    """Route initial user message to TranslationAgent."""
    try:
        return StringResult(
            result=next((agent for agent in participant_descriptions.keys() if agent == "TranslationAgent"), None),
            reason="Routing to TranslationAgent for initial translation."
        )
    except Exception as e:
        return StringResult(
            result=None,
            reason=f"Error routing to TranslationAgent: {e}"
        )


def route_translation_message(last_message: ChatMessageContent, participant_descriptions: dict) -> StringResult:
    """Route translated message to TriageAgent."""
    try:
        parsed = json.loads(last_message.content)
        response = parsed['response']
        print("[TranslationAgent] Translated message:", response)

        return StringResult(
            result=next((agent for agent in participant_descriptions.keys() if agent == "TriageAgent"), None),
            reason="Routing to TriageAgent for intent classification."
        )
    except Exception as e:
        return StringResult(
            result=None,
            reason=f"Error routing to TriageAgent: {e}"
        )


def route_triage_message(last_message: ChatMessageContent, participant_descriptions: dict) -> StringResult:
    """Route triage result to appropriate handler (CQA direct or Lumi for CLU)."""
    try:
        parsed = json.loads(last_message.content)
        
        # Handle CQA results (FAQ match)
        if parsed.get("type") == "cqa_result":
            print("[SYSTEM]: CQA result received, checking confidence...")
            confidence = parsed["response"]["answers"][0]["confidenceScore"]

            if confidence >= cqa_confidence:
                print(f"[TriageAgent]: CQA confidence {confidence} >= {cqa_confidence}, returning FAQ answer")
                return StringResult(
                    result=next((agent for agent in participant_descriptions.keys() if agent == "TranslationAgent"), None),
                    reason="Routing to TranslationAgent for final translation of CQA answer."
                )
            else:
                print(f"[TriageAgent]: CQA confidence {confidence} < {cqa_confidence}, falling back to Lumi")
                return StringResult(
                    result=next((agent for agent in participant_descriptions.keys() if agent == "Lumi"), None),
                    reason="Low CQA confidence, routing to Lumi for deeper analysis."
                )

        # Handle CLU results (intent extraction)
        if parsed.get("type") == "clu_result":
            print("[SYSTEM]: CLU result received, checking intent and entities...")
            intent = parsed["response"]["result"]["conversations"][0]["intents"][0]["name"]
            confidence = parsed["response"]["result"]["conversations"][0]["intents"][0]["confidenceScore"]
            
            print(f"[TriageAgent]: Detected intent '{intent}' with confidence {confidence}")
            
            if confidence >= confidence_threshold:
                print("[TriageAgent]: Routing to Lumi for SAGE agent selection...")
                return StringResult(
                    result=next((agent for agent in participant_descriptions.keys() if agent == "Lumi"), None),
                    reason="Routing to Lumi for IRI domain agent selection."
                )
            else:
                print(f"[TriageAgent]: Low CLU confidence {confidence}, routing to Lumi for clarification")
                return StringResult(
                    result=next((agent for agent in participant_descriptions.keys() if agent == "Lumi"), None),
                    reason="Low CLU confidence, Lumi will request clarification."
                )

    except Exception as e:
        print(f"[SYSTEM]: Error processing TriageAgent message: {e}")
        return StringResult(
            result=None,
            reason="Error processing TriageAgent message."
        )


def route_lumi_message(last_message: ChatMessageContent, participant_descriptions: dict) -> StringResult:
    """Route Lumi's decision to the appropriate SAGE agent."""
    try:
        parsed = json.loads(last_message.content)
        target_agent = parsed.get("target_agent")
        iri_domains = parsed.get("iri_domains", [])
        
        print(f"[Lumi] Routing to {target_agent} (IRI domains: {iri_domains})")
        
        # Validate target agent exists
        valid_agents = ["SciencesAgent", "GovernanceAgent", "AnalyticsAgent", "ExperienceAgent"]
        if target_agent not in valid_agents:
            print(f"[SYSTEM]: Unknown target agent '{target_agent}', defaulting to GovernanceAgent")
            target_agent = "GovernanceAgent"
        
        return StringResult(
            result=next((agent for agent in participant_descriptions.keys() if agent == target_agent), None),
            reason=f"Routing to {target_agent} for {', '.join(iri_domains)} domain expertise."
        )
    except Exception as e:
        print(f"[SYSTEM]: Error processing Lumi message: {e}")
        return StringResult(
            result=None,
            reason="Error processing Lumi message."
        )


def route_sage_agent_message(last_message: ChatMessageContent, participant_descriptions: dict) -> StringResult:
    """Route SAGE agent response back to TranslationAgent for final output."""
    try:
        parsed = json.loads(last_message.content)
        response = parsed.get("response", "")
        need_more_info = parsed.get("need_more_info", "False")
        
        print(f"[{last_message.name}]: Response received, need_more_info={need_more_info}")
        print(f"[TranslationAgent]: Translating response back to user language")
        
        return StringResult(
            result=next((agent for agent in participant_descriptions.keys() if agent == "TranslationAgent"), None),
            reason="Routing to TranslationAgent for final translation."
        )
    except Exception as e:
        print(f"[SYSTEM]: Error processing SAGE agent message: {e}")
        return StringResult(
            result=None,
            reason="Error processing SAGE agent message."
        )


# =============================================================================
# CUSTOM GROUP CHAT MANAGER - Orchestration logic
# =============================================================================

class CustomGroupChatManager(GroupChatManager):
    """
    Custom group chat manager for IRIS Symphony OSHA.
    Implements IRI-aware routing between SAGE agents.
    """
    
    async def filter_results(self, chat_history: ChatHistory) -> MessageResult:
        """Filter and return the final response."""
        if not chat_history:
            return MessageResult(
                result=ChatMessageContent(role="assistant", content="No messages in chat history."),
                reason="Chat history is empty."
            )

        last_message = chat_history[-1]
        return MessageResult(
            result=ChatMessageContent(role="assistant", content=last_message.content),
            reason="Returning the last agent's response."
        )

    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        """Determine if user input is needed (check need_more_info flag)."""
        if chat_history:
            last_message = chat_history[-1]
            try:
                parsed = json.loads(last_message.content)
                if parsed.get("need_more_info") == "True":
                    return BooleanResult(result=True, reason="Agent needs more information from user.")
            except:
                pass
        return BooleanResult(result=False, reason="No user input required.")

    async def select_next_agent(self, chat_history: ChatHistory, participant_descriptions: dict) -> StringResult:
        """
        Multi-agent orchestration for IRIS Symphony OSHA.
        Routes messages through: User → Translation → Triage → Lumi → SAGE Agents → Translation → User
        """
        last_message = chat_history[-1] if chat_history else None
        format_agent_response(last_message)

        # Route user messages to TranslationAgent
        if not last_message or last_message.role == AuthorRole.USER:
            print("[SYSTEM]: User message received, routing to TranslationAgent...")
            return route_user_message(participant_descriptions)

        # Route TranslationAgent → TriageAgent (initial) or terminate (final)
        elif last_message.name == "TranslationAgent":
            # Check if this is final translation (after SAGE agent response)
            if len(chat_history) > 3:
                print("[SYSTEM]: Final translation complete, terminating.")
                return StringResult(result=None, reason="Final translation complete.")
            print("[SYSTEM]: Initial translation complete, routing to TriageAgent...")
            return route_translation_message(last_message, participant_descriptions)

        # Route TriageAgent → Lumi or TranslationAgent (CQA direct)
        elif last_message.name == "TriageAgent":
            print("[SYSTEM]: Triage complete, routing based on result type...")
            return route_triage_message(last_message, participant_descriptions)

        # Route Lumi → SAGE Agent
        elif last_message.name == "Lumi":
            print("[SYSTEM]: Lumi routing to SAGE agent...")
            return route_lumi_message(last_message, participant_descriptions)

        # Route SAGE Agents → TranslationAgent
        elif last_message.name in ["SciencesAgent", "GovernanceAgent", "AnalyticsAgent", "ExperienceAgent"]:
            print(f"[SYSTEM]: {last_message.name} response received, routing to TranslationAgent...")
            return route_sage_agent_message(last_message, participant_descriptions)

        # Default: no routing
        print("[SYSTEM]: No valid routing logic found, terminating.")
        return StringResult(result=None, reason="No valid routing logic found.")

    async def should_terminate(self, chat_history: ChatHistory) -> BooleanResult:
        """Determine if chat should terminate."""
        if not chat_history:
            return BooleanResult(result=False, reason="No messages in chat history.")

        last_message = chat_history[-1]

        # Terminate after final translation
        if last_message.name == "TranslationAgent" and len(chat_history) > 3:
            print(f"[SYSTEM]: Final translation from {last_message.name}, terminating.")
            return BooleanResult(result=True, reason="Chat terminated after final translation.")

        return BooleanResult(result=False, reason="Chat continues.")


# =============================================================================
# SEMANTIC KERNEL ORCHESTRATOR - Main orchestration class
# =============================================================================

class SemanticKernelOrchestrator:
    """
    IRIS Symphony OSHA Semantic Kernel Orchestrator.
    
    Manages multi-agent conversations using Azure AI Foundry agents
    with IRI-aware routing through SAGE domain agents.
    """
    
    def __init__(
        self,
        client: AIProjectClient,
        model_name: str,
        project_endpoint: str,
        agent_ids: dict,
        fallback_function: Callable[[str, str, str], dict],
        max_retries: int = 3
    ):
        """Initialize the orchestrator."""
        self.client = client
        self.model_name = model_name
        self.project_endpoint = project_endpoint
        self.agent_ids = agent_ids
        self.fallback_function = fallback_function
        self.max_retries = max_retries

        # Initialize IRIS Symphony plugins (IRI Domain Agents)
        self.sciences_plugin = SciencesPlugin()
        self.regulatory_guidance_plugin = RegulatoryGuidancePlugin()
        self.recordability_plugin = RecordabilityPlugin()
        self.industry_analytics_plugin = IndustryAnalyticsPlugin()
        self.incident_management_plugin = IncidentManagementPlugin()
        self.document_generation_plugin = DocumentGenerationPlugin()

    async def initialize_agents(self) -> list:
        """
        Initialize IRIS Symphony OSHA agents from Azure AI Foundry.
        
        Returns list of agents in orchestration order:
        [TranslationAgent, TriageAgent, Lumi, SciencesAgent, GovernanceAgent, AnalyticsAgent, ExperienceAgent]
        """
        print("=" * 60)
        print("IRIS Symphony OSHA - Initializing Agents")
        print("=" * 60)
        
        # TranslationAgent - Multi-language support
        translation_agent_definition = await self.client.agents.get_agent(self.agent_ids["TRANSLATION_AGENT_ID"])
        translation_agent = AzureAIAgent(
            client=self.client,
            definition=translation_agent_definition,
            description="Translates messages to/from English for multi-language support.",
        )
        self.translation_agent = translation_agent

        # TriageAgent - CLU/CQA routing
        triage_agent_definition = await self.client.agents.get_agent(self.agent_ids["TRIAGE_AGENT_ID"])
        triage_agent = AzureAIAgent(
            client=self.client,
            definition=triage_agent_definition,
            description="Routes inquiries to CLU (intent) or CQA (FAQ) for classification.",
        )

        # Lumi - Primary orchestrator (IRI-aware routing)
        lumi_agent_definition = await self.client.agents.get_agent(self.agent_ids["LUMI_AGENT_ID"])
        lumi_agent = AzureAIAgent(
            client=self.client,
            definition=lumi_agent_definition,
            description="Primary orchestrator that routes to SAGE domain agents based on IRI methodology.",
        )

        # SciencesAgent - 📚 NIOSH, CDC, research, best practices
        sciences_agent_definition = await self.client.agents.get_agent(self.agent_ids["SCIENCES_AGENT_ID"])
        sciences_agent = AzureAIAgent(
            client=self.client,
            definition=sciences_agent_definition,
            description="Provides research-based guidance from NIOSH, CDC, and occupational health literature.",
            plugins=[self.sciences_plugin],
        )

        # GovernanceAgent - ⚖️ eCFR, Recordability Engine, regulations
        governance_agent_definition = await self.client.agents.get_agent(self.agent_ids["GOVERNANCE_AGENT_ID"])
        governance_agent = AzureAIAgent(
            client=self.client,
            definition=governance_agent_definition,
            description="Provides regulatory guidance from OSHA regulations (29 CFR 1904).",
            plugins=[self.regulatory_guidance_plugin, self.recordability_plugin],
        )

        # AnalyticsAgent - 📊 BLS, NAICS, industry risk data
        analytics_agent_definition = await self.client.agents.get_agent(self.agent_ids["ANALYTICS_AGENT_ID"])
        analytics_agent = AzureAIAgent(
            client=self.client,
            definition=analytics_agent_definition,
            description="Provides industry risk analytics from BLS injury rates and NAICS data.",
            plugins=[self.industry_analytics_plugin],
        )

        # ExperienceAgent - 🤝 Zone 2 incidents, documents (PII-protected)
        experience_agent_definition = await self.client.agents.get_agent(self.agent_ids["EXPERIENCE_AGENT_ID"])
        experience_agent = AzureAIAgent(
            client=self.client,
            definition=experience_agent_definition,
            description="Manages incident records and generates OSHA forms (Zone 2, PII-protected).",
            plugins=[self.incident_management_plugin, self.document_generation_plugin],
        )

        print("\n✅ Agents initialized successfully:")
        print(f"   TranslationAgent: {translation_agent.id}")
        print(f"   TriageAgent: {triage_agent.id}")
        print(f"   Lumi: {lumi_agent.id}")
        print(f"   📚 SciencesAgent: {sciences_agent.id}")
        print(f"   ⚖️ GovernanceAgent: {governance_agent.id}")
        print(f"   📊 AnalyticsAgent: {analytics_agent.id}")
        print(f"   🤝 ExperienceAgent: {experience_agent.id}")
        print("=" * 60)

        return [
            translation_agent,
            triage_agent,
            lumi_agent,
            sciences_agent,
            governance_agent,
            analytics_agent,
            experience_agent
        ]

    async def create_agent_group_chat(self) -> None:
        """Create the agent group chat with custom orchestration manager."""
        created_agents = await self.initialize_agents()
        print("Agents in group chat:", [agent.name for agent in created_agents])

        self.orchestration = GroupChatOrchestration(
            members=created_agents,
            manager=CustomGroupChatManager(),
        )

        print("✅ IRIS Symphony agent group chat created successfully.")

    async def process_message(self, task_content: str) -> tuple[str, bool]:
        """
        Process a message through the IRIS Symphony orchestration.
        
        Args:
            task_content: JSON string with query and language info
            
        Returns:
            Tuple of (response_text, need_more_info)
        """
        retry_count = 0
        last_exception = None
        need_more_info = False

        while retry_count < self.max_retries:
            print(f"\n[ATTEMPT {retry_count + 1}/{self.max_retries}] Starting orchestration...")
            runtime = InProcessRuntime()
            runtime.start()

            try:
                orchestration_result = await self.orchestration.invoke(
                    task=task_content,
                    runtime=runtime,
                )

                try:
                    # Timeout to avoid indefinite hangs
                    value = await orchestration_result.get(timeout=120)
                    print(f"\n{'=' * 40}\nFinal Result:\n{value.content}\n{'=' * 40}")

                    final_response = json.loads(value.content)
                    final_answer = final_response['response']['final_answer']
                    need_more_info = final_response['response'].get('need_more_info', False)
                    
                    print(f"[SYSTEM]: Final answer delivered, need_more_info={need_more_info}")
                    return final_answer, need_more_info

                except asyncio.TimeoutError:
                    print(f"[TIMEOUT]: Orchestration timed out after 120 seconds")
                    last_exception = {"type": "timeout", "message": "Orchestration timed out"}
                    retry_count += 1

                except Exception as e:
                    print(f"[EXCEPTION]: Orchestration failed: {e}")
                    last_exception = {"type": "exception", "message": str(e)}
                    retry_count += 1

            finally:
                try:
                    await runtime.stop_when_idle()
                except Exception as e:
                    print(f"[SHUTDOWN ERROR]: Runtime cleanup failed: {e}")

            await asyncio.sleep(1)

        # All retries exhausted
        print(f"[FAILURE]: Max retries ({self.max_retries}) reached.")
        return {"error": f"Orchestration failed: {last_exception}"}, need_more_info


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_agent_response(response: ChatMessageContent) -> str:
    """Pretty-print agent response for debugging."""
    if response is None:
        return ""
    try:
        formatted_content = json.dumps(json.loads(response.content), indent=2)
        print(f"[{response.name if response.name else 'USER'}]:\n{formatted_content}\n")
    except json.JSONDecodeError:
        print(f"[{response.name if response.name else 'USER'}]: {response.content}\n")
    return response.content if response else ""
