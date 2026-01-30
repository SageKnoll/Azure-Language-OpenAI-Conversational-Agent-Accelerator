# Copyright (c) Sagevia - IRIS Symphony OSHA
"""
IRIS Symphony OSHA - Agent Plugins
==================================
Semantic Kernel plugins for IRI domain agents.

IRI Domains:
- Sciences (📚): NIOSH, CDC, research guidance
- Governance (⚖️): eCFR, recordability, regulations
- Analytics (📊): BLS rates, NAICS, industry risk
- Experience (🤝): Incidents, documents (Zone 2, PII)
"""

from agents.sciences_plugin import SciencesPlugin
from agents.regulatory_guidance_plugin import RegulatoryGuidancePlugin
from agents.recordability_plugin import RecordabilityPlugin
from agents.industry_analytics_plugin import IndustryAnalyticsPlugin
from agents.incident_management_plugin import IncidentManagementPlugin
from agents.document_generation_plugin import DocumentGenerationPlugin

__all__ = [
    # Sciences Domain (📚)
    "SciencesPlugin",
    
    # Governance Domain (⚖️)
    "RegulatoryGuidancePlugin",
    "RecordabilityPlugin",
    
    # Analytics Domain (📊)
    "IndustryAnalyticsPlugin",
    
    # Experience Domain (🤝)
    "IncidentManagementPlugin",
    "DocumentGenerationPlugin",
]
