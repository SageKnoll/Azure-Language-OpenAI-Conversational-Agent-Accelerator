# Copyright (c) Sagevia - IRIS Symphony OSHA
"""
Regulatory Guidance Plugin - IRI Governance Domain (⚖️)
=======================================================
Searches OSHA regulations in 29 CFR 1904 via the Zone 1 eCFR Search API.

Capabilities:
- Semantic search of eCFR regulatory text
- Retrieve specific CFR sections
- Explain regulatory requirements with citations
"""

import os
import httpx
from typing import Annotated
from semantic_kernel.functions import kernel_function


class RegulatoryGuidancePlugin:
    """Plugin for searching OSHA regulations via eCFR Search API."""
    
    def __init__(self):
        """Initialize the Regulatory Guidance plugin."""
        self.ecfr_api_url = os.environ.get(
            "IRIS_ZONE1_ECFR_URL",
            "https://ca-svo-ecfr-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io"
        )
    
    @kernel_function(
        name="search_ecfr",
        description="Search OSHA regulations (29 CFR 1904) for guidance on a specific topic."
    )
    def search_ecfr(
        self,
        query: Annotated[str, "The regulatory topic to search for (e.g., 'first aid', 'days away', 'work-related')"]
    ) -> str:
        """
        Search the eCFR for relevant OSHA recordkeeping regulations.
        
        Args:
            query: The search query
            
        Returns:
            Relevant regulatory text with CFR citations
        """
        try:
            # Call Zone 1 eCFR Search API
            response = httpx.get(
                f"{self.ecfr_api_url}/search",
                params={"q": query, "top_k": 3},
                timeout=30.0
            )
            response.raise_for_status()
            results = response.json()
            
            if not results.get("results"):
                return f"No regulatory guidance found for '{query}'. Try different search terms."
            
            # Format results
            output = f"Regulatory Guidance for '{query}':\n\n"
            for i, result in enumerate(results["results"], 1):
                output += f"[{i}] {result.get('citation', 'CFR')}\n"
                output += f"    {result.get('text', '')[:500]}...\n\n"
            
            return output
            
        except httpx.RequestError as e:
            # Fallback to static guidance if API unavailable
            return self._get_static_guidance(query)
        except Exception as e:
            return f"Error searching regulations: {str(e)}"
    
    @kernel_function(
        name="get_cfr_section",
        description="Retrieve a specific CFR section by citation (e.g., '1904.7(a)')."
    )
    def get_cfr_section(
        self,
        citation: Annotated[str, "The CFR section citation (e.g., '1904.7', '1904.5(b)(2)')"]
    ) -> str:
        """
        Retrieve a specific CFR section.
        
        Args:
            citation: The CFR section number
            
        Returns:
            The regulatory text for that section
        """
        try:
            response = httpx.get(
                f"{self.ecfr_api_url}/section/{citation}",
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            return f"29 CFR {citation}:\n{result.get('text', 'Section not found')}"
            
        except Exception as e:
            return self._get_static_section(citation)
    
    def _get_static_guidance(self, query: str) -> str:
        """Fallback static guidance when API is unavailable."""
        guidance_map = {
            "first aid": (
                "Per 29 CFR 1904.7(a), first aid treatments are NOT recordable. "
                "First aid includes: bandages, butterfly closures, finger guards, "
                "non-prescription medications at nonprescription strength, tetanus shots, "
                "wound cleaning, hot/cold therapy, rigid stays, and more. "
                "See the complete list in 1904.7(a)."
            ),
            "medical treatment": (
                "Per 29 CFR 1904.7(a), medical treatment beyond first aid triggers recording. "
                "Examples: prescription medications, sutures/stitches, physical therapy, "
                "chiropractic treatment. If treatment goes beyond the first aid list, "
                "the case meets the recording criteria."
            ),
            "days away": (
                "Per 29 CFR 1904.7(b)(3), count the number of calendar days the employee "
                "was unable to work due to the injury or illness. Do not count the day of "
                "injury. Cap at 180 days. Include weekends and holidays if the employee "
                "would not have been able to work those days."
            ),
            "work-related": (
                "Per 29 CFR 1904.5, an injury is work-related if an event or exposure in "
                "the work environment caused or contributed to it, or significantly aggravated "
                "a pre-existing condition. Exceptions exist for voluntary wellness activities, "
                "eating/drinking, personal tasks, and more - see 1904.5(b)(2)."
            ),
            "recording criteria": (
                "Per 29 CFR 1904.7, record an injury/illness if it results in: "
                "death, days away from work, restricted work or transfer, "
                "medical treatment beyond first aid, loss of consciousness, "
                "or significant injury/illness diagnosed by a physician."
            )
        }
        
        query_lower = query.lower()
        for key, guidance in guidance_map.items():
            if key in query_lower:
                return guidance
        
        return f"Unable to find guidance for '{query}'. Please try a more specific search term."
    
    def _get_static_section(self, citation: str) -> str:
        """Fallback static section text when API is unavailable."""
        sections = {
            "1904.7": "General recording criteria for work-related injuries and illnesses.",
            "1904.7(a)": "First aid list - treatments that do NOT make a case recordable.",
            "1904.5": "Determination of work-relatedness.",
            "1904.5(b)(2)": "Exceptions to work-relatedness presumption.",
            "1904.29": "Forms and privacy concern cases.",
            "1904.32": "Annual summary (Form 300A) requirements.",
            "1904.39": "Reporting fatalities and severe injuries to OSHA.",
            "1904.41": "Electronic submission requirements."
        }
        
        for key, desc in sections.items():
            if citation.startswith(key) or key.startswith(citation):
                return f"29 CFR {key}: {desc}\n(Full text available when eCFR API is online)"
        
        return f"Section 29 CFR {citation} not found in cache. Check the eCFR at ecfr.gov."
