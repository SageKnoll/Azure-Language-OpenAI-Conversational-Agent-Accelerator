# Copyright (c) Sagevia - IRIS Symphony OSHA
"""
Sciences Plugin - IRI Sciences Domain (📚)
==========================================
Provides research-based guidance from NIOSH, CDC, and occupational health literature.

Capabilities:
- NIOSH exposure limits (RELs)
- CDC guidelines and surveillance data
- Best practices beyond regulatory minimums
- Research summaries on workplace hazards
"""

import os
import httpx
from typing import Annotated
from semantic_kernel.functions import kernel_function


class SciencesPlugin:
    """Plugin for IRI Sciences domain - NIOSH, CDC, research guidance."""
    
    def __init__(self):
        """Initialize the Sciences plugin."""
        # Future: Connect to NIOSH API or knowledge base
        self.niosh_base_url = os.environ.get("NIOSH_API_URL", "")
    
    @kernel_function(
        name="get_niosh_guidance",
        description="Get NIOSH research recommendations and exposure limits for a specific hazard or topic."
    )
    def get_niosh_guidance(
        self,
        topic: Annotated[str, "The hazard or topic to look up (e.g., 'silica', 'noise', 'heat stress')"]
    ) -> str:
        """
        Retrieve NIOSH guidance on a specific occupational health topic.
        
        Args:
            topic: The hazard or topic to search for
            
        Returns:
            NIOSH recommendations and exposure limits
        """
        # Placeholder - in production, this would query NIOSH resources or a knowledge base
        niosh_guidance = {
            "silica": {
                "niosh_rel": "0.05 mg/m³ (50 µg/m³) as a TWA for up to 10 hours",
                "osha_pel": "0.05 mg/m³ (50 µg/m³) as a TWA for 8 hours",
                "note": "NIOSH REL and OSHA PEL are currently aligned for respirable crystalline silica",
                "source": "NIOSH Criteria for a Recommended Standard: Occupational Exposure to Crystalline Silica (2002)"
            },
            "noise": {
                "niosh_rel": "85 dBA TWA for 8 hours, with 3 dB exchange rate",
                "osha_pel": "90 dBA TWA for 8 hours, with 5 dB exchange rate",
                "note": "NIOSH recommends more protective limits than OSHA requires",
                "source": "NIOSH Criteria for a Recommended Standard: Occupational Noise Exposure (1998)"
            },
            "heat_stress": {
                "niosh_rel": "Wet Bulb Globe Temperature (WBGT) limits based on workload",
                "guidance": "Light work: 30°C WBGT, Moderate: 27.5°C, Heavy: 25°C",
                "note": "OSHA has no specific PEL for heat; uses General Duty Clause",
                "source": "NIOSH Criteria for a Recommended Standard: Occupational Exposure to Heat and Hot Environments (2016)"
            }
        }
        
        topic_lower = topic.lower().replace(" ", "_")
        if topic_lower in niosh_guidance:
            guidance = niosh_guidance[topic_lower]
            return (
                f"NIOSH Guidance for {topic}:\n"
                f"- NIOSH REL: {guidance.get('niosh_rel', 'Not specified')}\n"
                f"- OSHA PEL: {guidance.get('osha_pel', 'Not specified')}\n"
                f"- Note: {guidance.get('note', '')}\n"
                f"- Source: {guidance.get('source', 'NIOSH')}"
            )
        else:
            return f"No specific NIOSH guidance found for '{topic}'. Consider searching the NIOSH Pocket Guide or CDC/NIOSH website for current recommendations."

    @kernel_function(
        name="compare_regulatory_vs_recommended",
        description="Compare OSHA regulatory requirements with NIOSH research recommendations for a hazard."
    )
    def compare_regulatory_vs_recommended(
        self,
        hazard: Annotated[str, "The occupational hazard to compare (e.g., 'lead', 'benzene')"]
    ) -> str:
        """
        Compare regulatory requirements (OSHA PEL) with research recommendations (NIOSH REL).
        
        Args:
            hazard: The hazard to compare
            
        Returns:
            Comparison of OSHA requirements vs NIOSH recommendations
        """
        comparisons = {
            "lead": {
                "osha_pel": "50 µg/m³",
                "niosh_rel": "50 µg/m³",
                "acgih_tlv": "50 µg/m³",
                "note": "All three agencies align on 50 µg/m³, but blood lead monitoring triggers differ"
            },
            "benzene": {
                "osha_pel": "1 ppm TWA, 5 ppm STEL",
                "niosh_rel": "0.1 ppm TWA",
                "acgih_tlv": "0.5 ppm TWA, 2.5 ppm STEL",
                "note": "NIOSH recommends 10x lower limit than OSHA due to carcinogenicity"
            },
            "formaldehyde": {
                "osha_pel": "0.75 ppm TWA, 2 ppm STEL",
                "niosh_rel": "0.016 ppm TWA (lowest feasible concentration)",
                "acgih_tlv": "0.1 ppm Ceiling",
                "note": "NIOSH recommends minimizing exposure as low as feasible due to cancer risk"
            }
        }
        
        hazard_lower = hazard.lower()
        if hazard_lower in comparisons:
            comp = comparisons[hazard_lower]
            return (
                f"Regulatory vs Recommended Limits for {hazard}:\n"
                f"- OSHA PEL (Legal requirement): {comp['osha_pel']}\n"
                f"- NIOSH REL (Research recommendation): {comp['niosh_rel']}\n"
                f"- ACGIH TLV (Professional recommendation): {comp['acgih_tlv']}\n"
                f"- Key difference: {comp['note']}\n\n"
                f"Remember: OSHA PELs are legal minimums. NIOSH RELs represent best available science."
            )
        else:
            return f"No comparison data available for '{hazard}'. Check the NIOSH Pocket Guide for current limits."

    @kernel_function(
        name="get_prevention_best_practices",
        description="Get evidence-based prevention strategies for a workplace hazard."
    )
    def get_prevention_best_practices(
        self,
        hazard_type: Annotated[str, "Type of hazard (e.g., 'ergonomic', 'chemical', 'biological')"]
    ) -> str:
        """
        Retrieve evidence-based prevention strategies from occupational health research.
        
        Args:
            hazard_type: The category of hazard
            
        Returns:
            Prevention hierarchy and best practices
        """
        best_practices = {
            "ergonomic": [
                "Engineering controls: Adjustable workstations, mechanical lifting aids",
                "Administrative controls: Job rotation, microbreaks every 30-60 minutes",
                "Training: Proper lifting techniques, early symptom reporting",
                "Source: NIOSH Elements of Ergonomics Programs"
            ],
            "chemical": [
                "Elimination/Substitution: Replace with less hazardous chemicals",
                "Engineering controls: Local exhaust ventilation, enclosed processes",
                "Administrative controls: Reduce exposure time, rotate workers",
                "PPE: Respirators, gloves, protective clothing (last resort)",
                "Source: NIOSH Hierarchy of Controls"
            ],
            "biological": [
                "Engineering controls: Ventilation, HEPA filtration, UV germicidal",
                "Administrative controls: Vaccination programs, exposure protocols",
                "PPE: N95 respirators, gowns, face shields",
                "Source: CDC/NIOSH Guidelines for Infection Control"
            ],
            "noise": [
                "Engineering controls: Sound barriers, equipment maintenance, vibration isolation",
                "Administrative controls: Limit exposure time, hearing conservation program",
                "PPE: Earplugs (NRR 25-33), earmuffs",
                "Source: NIOSH Criteria for a Recommended Standard: Occupational Noise Exposure"
            ]
        }
        
        hazard_lower = hazard_type.lower()
        if hazard_lower in best_practices:
            practices = best_practices[hazard_lower]
            return f"Best Practices for {hazard_type} Hazards:\n" + "\n".join(f"• {p}" for p in practices)
        else:
            return (
                f"General Prevention Hierarchy (applies to all hazards):\n"
                f"1. Elimination - Remove the hazard entirely\n"
                f"2. Substitution - Replace with less hazardous alternative\n"
                f"3. Engineering Controls - Isolate people from hazard\n"
                f"4. Administrative Controls - Change the way people work\n"
                f"5. PPE - Protect the worker (last resort)\n\n"
                f"Source: NIOSH Hierarchy of Controls"
            )
