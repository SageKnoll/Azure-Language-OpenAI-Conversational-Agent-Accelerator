# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# Modified for IRIS Symphony OSHA by Sagevia
"""
IRIS Symphony OSHA - Handoff Client
===================================
Local script to test HandoffOrchestration with OSHA agents.
Run with: python -m handoff_client
"""

import os
import asyncio
from semantic_kernel.agents import AzureAIAgent, OrchestrationHandoffs, HandoffOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import AuthorRole, ChatMessageContent
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
}

# Confidence threshold
confidence_threshold = float(os.environ.get("CLU_CONFIDENCE_THRESHOLD", "0.7"))


def human_response_function() -> ChatMessageContent:
    """Get input from user."""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


def agent_response_callback(message: ChatMessageContent) -> None:
    """Print agent responses."""
    if message.content:
        print(f"{message.name}: {message.content}")


async def main():
    """Test IRIS Symphony OSHA handoff orchestration."""
    async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as creds:
        async with AzureAIAgent.create_client(credential=creds, endpoint=PROJECT_ENDPOINT) as client:
            
            # Initialize TriageAgent
            triage_def = await client.agents.get_agent(AGENT_IDS["TRIAGE_AGENT_ID"])
            triage_agent = AzureAIAgent(
                client=client,
                definition=triage_def,
                description="Routes OSHA questions to appropriate SAGE agents based on intent"
            )

            # Initialize Lumi (Primary Orchestrator)
            lumi_def = await client.agents.get_agent(AGENT_IDS["LUMI_AGENT_ID"])
            lumi_agent = AzureAIAgent(
                client=client,
                definition=lumi_def,
                description="Primary orchestrator that routes to IRI domain agents"
            )

            # Initialize SciencesAgent - 📚 NIOSH, CDC, research
            sciences_def = await client.agents.get_agent(AGENT_IDS["SCIENCES_AGENT_ID"])
            sciences_agent = AzureAIAgent(
                client=client,
                definition=sciences_def,
                description="Provides research-based guidance from NIOSH, CDC. Use SciencesPlugin for exposure limits and best practices. Returns JSON: {'response': <guidance>, 'terminated': 'True', 'need_more_info': <bool>}",
                plugins=[SciencesPlugin()],
            )

            # Initialize GovernanceAgent - ⚖️ eCFR, Recordability
            governance_def = await client.agents.get_agent(AGENT_IDS["GOVERNANCE_AGENT_ID"])
            governance_agent = AzureAIAgent(
                client=client,
                definition=governance_def,
                description="Provides OSHA regulatory guidance from 29 CFR 1904. Use RegulatoryGuidancePlugin for eCFR search and RecordabilityPlugin for Q0-Q4 logic. Returns JSON: {'response': <guidance>, 'terminated': 'True', 'need_more_info': <bool>}",
                plugins=[RegulatoryGuidancePlugin(), RecordabilityPlugin()],
            )

            # Initialize AnalyticsAgent - 📊 BLS, NAICS
            analytics_def = await client.agents.get_agent(AGENT_IDS["ANALYTICS_AGENT_ID"])
            analytics_agent = AzureAIAgent(
                client=client,
                definition=analytics_def,
                description="Provides industry risk data from BLS injury rates and NAICS codes. Use IndustryAnalyticsPlugin. Returns JSON: {'response': <data>, 'terminated': 'True', 'need_more_info': <bool>}",
                plugins=[IndustryAnalyticsPlugin()],
            )

            # Initialize ExperienceAgent - 🤝 Incidents, Documents (Zone 2)
            experience_def = await client.agents.get_agent(AGENT_IDS["EXPERIENCE_AGENT_ID"])
            experience_agent = AzureAIAgent(
                client=client,
                definition=experience_def,
                description="Manages incident records and generates OSHA forms. Use IncidentManagementPlugin and DocumentGenerationPlugin. Zone 2 PII-protected. Returns JSON: {'response': <result>, 'terminated': 'True', 'need_more_info': <bool>}",
                plugins=[IncidentManagementPlugin(), DocumentGenerationPlugin()],
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
            print("=" * 50)

            # Define handoffs between agents
            handoffs = (
                OrchestrationHandoffs()
                # Triage routes to Lumi for all intents
                .add(
                    source_agent=triage_agent.name,
                    target_agent=lumi_agent.name,
                    description="Transfer to Lumi when CLU extracts an intent. Lumi will route to the appropriate SAGE agent."
                )
                # Lumi routes to SAGE agents based on IRI domain
                .add_many(
                    source_agent=lumi_agent.name,
                    target_agents={
                        sciences_agent.name: "Transfer for research questions about NIOSH recommendations, exposure limits, or best practices beyond OSHA minimums.",
                        governance_agent.name: "Transfer for regulatory questions about OSHA recordkeeping, recordability determinations, first aid vs medical treatment, or CFR interpretations.",
                        analytics_agent.name: "Transfer for industry risk questions about BLS injury rates, NAICS codes, or DART/TCIR calculations.",
                        experience_agent.name: "Transfer for incident-specific operations like creating records, generating forms, or tracking days away."
                    }
                )
                # SAGE agents can route back to Lumi for cross-domain questions
                .add(
                    source_agent=sciences_agent.name,
                    target_agent=lumi_agent.name,
                    description="Transfer back to Lumi if the question requires regulatory or analytics expertise, not just research guidance."
                )
                .add(
                    source_agent=governance_agent.name,
                    target_agent=lumi_agent.name,
                    description="Transfer back to Lumi if the question requires research or analytics expertise beyond regulatory interpretation."
                )
                .add(
                    source_agent=analytics_agent.name,
                    target_agent=lumi_agent.name,
                    description="Transfer back to Lumi if the question requires regulatory or research expertise beyond data analysis."
                )
                .add(
                    source_agent=experience_agent.name,
                    target_agent=lumi_agent.name,
                    description="Transfer back to Lumi if the question requires regulatory, research, or analytics expertise beyond incident management."
                )
            )

            # Create handoff orchestration
            handoff_orchestration = HandoffOrchestration(
                members=[
                    triage_agent,
                    lumi_agent,
                    sciences_agent,
                    governance_agent,
                    analytics_agent,
                    experience_agent,
                ],
                handoffs=handoffs,
                agent_response_callback=agent_response_callback,
                human_response_function=human_response_function,
            )

            # Test queries
            test_queries = [
                "Is getting 4 stitches on a cut recordable?",
                "What does NIOSH recommend for silica exposure limits?",
                "What are the injury rates for plumbing contractors?",
                "When do I post the Form 300A?",
            ]

            runtime = InProcessRuntime()
            runtime.start()

            print(f"\nTest: {test_queries[0]}")
            print("-" * 50)

            result = await handoff_orchestration.invoke(
                task=test_queries[0],
                runtime=runtime,
            )

            try:
                value = await result.get()
                print(f"\n{'=' * 50}")
                print(f"RESULT: {value}")
                print("=" * 50)
            except Exception as e:
                print(f"[ERROR]: {e}")

            await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())
    print("\n✅ IRIS Symphony OSHA handoff test complete.")
