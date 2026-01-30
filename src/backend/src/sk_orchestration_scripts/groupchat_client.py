# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# Modified for IRIS Symphony OSHA by Sagevia
"""
IRIS Symphony OSHA - Group Chat Client
======================================
Local script to test GroupChatOrchestration with OSHA agents.
Run with: python -m groupchat_client
"""

import os
import json
import asyncio
from semantic_kernel.agents import AzureAIAgent, GroupChatOrchestration, GroupChatManager, BooleanResult, StringResult, MessageResult
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import AuthorRole, ChatMessageContent, ChatHistory
from azure.identity.aio import DefaultAzureCredential

# IRIS Symphony OSHA Plugins
from agents.sciences_plugin import SciencesPlugin
from agents.regulatory_guidance_plugin import RegulatoryGuidancePlugin
from agents.recordability_plugin import RecordabilityPlugin
from agents.industry_analytics_plugin import IndustryAnalyticsPlugin
from agents.incident_management_plugin import IncidentManagementPlugin
from agents.document_generation_plugin import DocumentGenerationPlugin

from dotenv import load_dotenv
load_dotenv()

# Environment variables
PROJECT_ENDPOINT = os.environ.get("AGENTS_PROJECT_ENDPOINT")
MODEL_NAME = os.environ.get("AOAI_DEPLOYMENT")

# Agent IDs from AI Foundry
AGENT_IDS = {
    "TRIAGE_AGENT_ID": os.environ.get("TRIAGE_AGENT_ID"),
    "LUMI_AGENT_ID": os.environ.get("LUMI_AGENT_ID"),
    "SCIENCES_AGENT_ID": os.environ.get("SCIENCES_AGENT_ID"),
    "GOVERNANCE_AGENT_ID": os.environ.get("GOVERNANCE_AGENT_ID"),
    "ANALYTICS_AGENT_ID": os.environ.get("ANALYTICS_AGENT_ID"),
    "EXPERIENCE_AGENT_ID": os.environ.get("EXPERIENCE_AGENT_ID"),
    "TRANSLATION_AGENT_ID": os.environ.get("TRANSLATION_AGENT_ID"),
    # Legacy mappings for compatibility
    "HEAD_SUPPORT_AGENT_ID": os.environ.get("LUMI_AGENT_ID"),
}

# Confidence thresholds
confidence_threshold = float(os.environ.get("CLU_CONFIDENCE_THRESHOLD", "0.7"))
cqa_confidence = float(os.environ.get("CQA_CONFIDENCE", "0.8"))


class CustomGroupChatManager(GroupChatManager):
    """Custom group chat manager for IRIS Symphony OSHA."""
    
    async def filter_results(self, chat_history: ChatHistory) -> MessageResult:
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
        return BooleanResult(result=False, reason="No user input needed.")

    async def select_next_agent(self, chat_history, participant_descriptions):
        """Route messages through IRIS Symphony agent pipeline."""
        last_message = chat_history[-1] if chat_history else None
        format_agent_response(last_message)

        # User → TranslationAgent
        if not last_message or last_message.role == AuthorRole.USER:
            if len(chat_history) == 1:
                print("[SYSTEM]: User message, routing to TranslationAgent...")
                return StringResult(
                    result=next((a for a in participant_descriptions.keys() if a == "TranslationAgent"), None),
                    reason="Initial translation."
                )

        # TranslationAgent → TriageAgent
        elif last_message.name == "TranslationAgent":
            try:
                parsed = json.loads(last_message.content)
                print("[TranslationAgent] Translated:", parsed.get('response'))
                return StringResult(
                    result=next((a for a in participant_descriptions.keys() if a == "TriageAgent"), None),
                    reason="Routing to TriageAgent."
                )
            except Exception as e:
                return StringResult(result=None, reason=f"Error: {e}")

        # TriageAgent → Lumi or TranslationAgent (CQA)
        elif last_message.name == "TriageAgent":
            try:
                parsed = json.loads(last_message.content)
                
                if parsed.get("type") == "cqa_result":
                    print("[SYSTEM]: CQA result, terminating.")
                    return StringResult(result=None, reason="CQA result received.")
                
                if parsed.get("type") == "clu_result":
                    intent = parsed["response"]["result"]["conversations"][0]["intents"][0]["name"]
                    print(f"[TriageAgent]: Intent '{intent}', routing to Lumi...")
                    return StringResult(
                        result=next((a for a in participant_descriptions.keys() if a == "Lumi"), None),
                        reason="Routing to Lumi for SAGE agent selection."
                    )
            except Exception as e:
                print(f"[ERROR]: {e}")
                return StringResult(result=None, reason="Error processing triage.")

        # Lumi → SAGE Agent
        elif last_message.name == "Lumi":
            try:
                parsed = json.loads(last_message.content)
                target = parsed.get("target_agent")
                print(f"[Lumi]: Routing to {target}")
                return StringResult(
                    result=next((a for a in participant_descriptions.keys() if a == target), None),
                    reason=f"Routing to {target}."
                )
            except Exception as e:
                return StringResult(result=None, reason=f"Error: {e}")

        # SAGE Agents → TranslationAgent
        elif last_message.name in ["SciencesAgent", "GovernanceAgent", "AnalyticsAgent", "ExperienceAgent"]:
            print(f"[{last_message.name}]: Response received, routing to TranslationAgent...")
            return StringResult(
                result=next((a for a in participant_descriptions.keys() if a == "TranslationAgent"), None),
                reason="Final translation."
            )

        print("[SYSTEM]: No routing match, terminating.")
        return StringResult(result=None, reason="No routing logic matched.")

    async def should_terminate(self, chat_history):
        last_message = chat_history[-1] if chat_history else None
        if not last_message:
            return BooleanResult(result=False, reason="No messages.")
        
        if last_message.name == "TranslationAgent" and len(chat_history) > 3:
            return BooleanResult(result=True, reason="Final translation complete.")
        
        return BooleanResult(result=False, reason="Continue.")


def agent_response_callback(message: ChatMessageContent) -> None:
    """Print agent messages."""
    print(f"**{message.name}**\n{message.content}")


async def main():
    """Test IRIS Symphony OSHA orchestration."""
    async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as creds:
        async with AzureAIAgent.create_client(credential=creds, endpoint=PROJECT_ENDPOINT) as client:
            
            # Initialize agents
            triage_def = await client.agents.get_agent(AGENT_IDS["TRIAGE_AGENT_ID"])
            triage_agent = AzureAIAgent(
                client=client,
                definition=triage_def,
                description="Routes to CLU/CQA for classification",
            )

            lumi_def = await client.agents.get_agent(AGENT_IDS["LUMI_AGENT_ID"])
            lumi_agent = AzureAIAgent(
                client=client,
                definition=lumi_def,
                description="Primary orchestrator for IRI domain routing",
            )

            sciences_def = await client.agents.get_agent(AGENT_IDS["SCIENCES_AGENT_ID"])
            sciences_agent = AzureAIAgent(
                client=client,
                definition=sciences_def,
                description="📚 NIOSH/CDC research and best practices",
                plugins=[SciencesPlugin()],
            )

            governance_def = await client.agents.get_agent(AGENT_IDS["GOVERNANCE_AGENT_ID"])
            governance_agent = AzureAIAgent(
                client=client,
                definition=governance_def,
                description="⚖️ OSHA regulations and recordability",
                plugins=[RegulatoryGuidancePlugin(), RecordabilityPlugin()],
            )

            analytics_def = await client.agents.get_agent(AGENT_IDS["ANALYTICS_AGENT_ID"])
            analytics_agent = AzureAIAgent(
                client=client,
                definition=analytics_def,
                description="📊 BLS injury rates and industry risk",
                plugins=[IndustryAnalyticsPlugin()],
            )

            experience_def = await client.agents.get_agent(AGENT_IDS["EXPERIENCE_AGENT_ID"])
            experience_agent = AzureAIAgent(
                client=client,
                definition=experience_def,
                description="🤝 Incident management (Zone 2, PII)",
                plugins=[IncidentManagementPlugin(), DocumentGenerationPlugin()],
            )

            translation_def = await client.agents.get_agent(AGENT_IDS["TRANSLATION_AGENT_ID"])
            translation_agent = AzureAIAgent(
                client=client,
                definition=translation_def,
                description="Multi-language translation",
            )

            print("\n" + "=" * 50)
            print("IRIS Symphony OSHA Agents Initialized")
            print("=" * 50)
            print(f"  TriageAgent: {triage_agent.id}")
            print(f"  Lumi: {lumi_agent.id}")
            print(f"  📚 SciencesAgent: {sciences_agent.id}")
            print(f"  ⚖️ GovernanceAgent: {governance_agent.id}")
            print(f"  📊 AnalyticsAgent: {analytics_agent.id}")
            print(f"  🤝 ExperienceAgent: {experience_agent.id}")
            print(f"  TranslationAgent: {translation_agent.id}")
            print("=" * 50)

            agents = [
                translation_agent,
                triage_agent,
                lumi_agent,
                sciences_agent,
                governance_agent,
                analytics_agent,
                experience_agent
            ]

            orchestration = GroupChatOrchestration(
                members=agents,
                manager=CustomGroupChatManager(),
            )

            # Test queries
            test_queries = [
                {
                    "query": "Is an employee getting 4 stitches recordable?",
                    "to": "english"
                },
                {
                    "query": "What are the injury rates for NAICS 238220?",
                    "to": "english"
                },
                {
                    "query": "¿Cuándo debo publicar el Formulario 300A?",
                    "to": "english"
                }
            ]

            for test in test_queries[:1]:  # Run first test
                print(f"\n{'=' * 50}")
                print(f"TEST: {test['query']}")
                print("=" * 50)

                for attempt in range(1, 4):
                    print(f"\n[ATTEMPT {attempt}] Starting runtime...")
                    runtime = InProcessRuntime(ignore_unhandled_exceptions=False)
                    runtime.start()

                    try:
                        result = await orchestration.invoke(
                            task=json.dumps(test),
                            runtime=runtime,
                        )
                        value = await result.get(timeout=60)
                        print(f"\n***** RESULT *****\n{value}")
                        break
                    except Exception as e:
                        print(f"[ERROR]: {e}")
                    finally:
                        try:
                            await runtime.stop_when_idle()
                        except Exception as e:
                            print(f"[SHUTDOWN ERROR]: {e}")
                    await asyncio.sleep(2)


def format_agent_response(response):
    """Pretty-print agent response."""
    if response is None:
        return ""
    try:
        formatted = json.dumps(json.loads(response.content), indent=2)
        print(f"[{response.name or 'USER'}]:\n{formatted}\n")
    except json.JSONDecodeError:
        print(f"[{response.name or 'USER'}]: {response.content}\n")
    return response.content


if __name__ == "__main__":
    asyncio.run(main())
    print("\n✅ IRIS Symphony OSHA orchestration test complete.")
