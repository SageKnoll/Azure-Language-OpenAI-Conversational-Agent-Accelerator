# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# Modified for IRIS Symphony - OSHA Recordkeeping
"""
OSHA Recordkeeping function hooks for each CLU intent.

These hooks are called when CLU recognizes an intent with high confidence,
bypassing full Lumi orchestration for deterministic responses.
"""
import os
import logging
import httpx

_logger = logging.getLogger(__name__)

# Zone 1 service URLs
RECORDABILITY_URL = os.environ.get(
    "IRIS_ZONE1_RECORDABILITY_URL",
    "https://ca-svo-recordability-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io"
)
ECFR_URL = os.environ.get(
    "IRIS_ZONE1_ECFR_URL",
    "https://ca-svo-ecfr-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io"
)
ANALYTICS_URL = os.environ.get(
    "IRIS_ZONE1_ANALYTICS_URL",
    "https://ca-svo-analytics-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io"
)


def get_entity(entities: list[dict], entity_name: str) -> str:
    """Extract entity value from CLU entities list."""
    triage_agent = os.environ.get("ROUTER_TYPE") == "TRIAGE_AGENT"

    for ent in entities:
        if (triage_agent and ent.get("name") == entity_name) or (ent.get("category") == entity_name):
            return ent["text"]
    return None


def get_injury_type(entities: list[dict]) -> str:
    """Extract InjuryType entity."""
    return get_entity(entities, "InjuryType")


def get_treatment_type(entities: list[dict]) -> str:
    """Extract TreatmentType entity."""
    return get_entity(entities, "TreatmentType")


def get_naics_code(entities: list[dict]) -> str:
    """Extract NAICSCode entity."""
    return get_entity(entities, "NAICSCode")


def get_form_type(entities: list[dict]) -> str:
    """Extract FormType entity."""
    return get_entity(entities, "FormType")


def RecordabilityQuestion(entities: list[dict]) -> str:
    """
    Handle recordability questions.
    Routes to Recordability Engine for Q0-Q4 decision logic.
    """
    injury_type = get_injury_type(entities)
    treatment_type = get_treatment_type(entities)

    if not injury_type and not treatment_type:
        return (
            "To assist with recordability assessments, I need more information about the incident. "
            "What type of injury or illness occurred, and what treatment was provided?"
        )

    try:
        # Call Recordability Engine
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{RECORDABILITY_URL}/evaluate",
                json={
                    "injury_type": injury_type,
                    "treatment": treatment_type,
                }
            )
            response.raise_for_status()
            result = response.json()

            recordable = result.get("recordable", False)
            reasoning = result.get("reasoning", "")
            citations = result.get("citations", [])

            citation_text = ", ".join(citations) if citations else "29 CFR 1904.7"

            if recordable:
                return (
                    f"Based on the information provided, this case appears to be **recordable**. "
                    f"{reasoning} See {citation_text}."
                )
            else:
                return (
                    f"Based on the information provided, this case does **not appear to be recordable**. "
                    f"{reasoning} See {citation_text}."
                )

    except Exception as e:
        _logger.error(f"Recordability Engine call failed: {e}")
        return (
            "I encountered an error checking recordability. "
            "Please provide more details about the injury and treatment, "
            "and I'll have the full team evaluate your question."
        )

def RecordabilityQuestion(entities: list[dict]) -> str:
    """
    Handle recordability questions.
    Routes to Recordability Engine for regulatory criteria matching and Q0-Q4 decision logic.
    Presents facts and regulation - user determines outcome via UI.
    
    """
    injury_type = get_injury_type(entities)
    treatment_type = get_treatment_type(entities)

    if not injury_type and not treatment_type:
        return (
            "To evaluate recordability criteria, I need more information about the incident. "
            "What type of injury or illness occurred, and what treatment was provided?"
        )

    try:
        # Call Recordability Engine
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{RECORDABILITY_URL}/evaluate",
                json={
                    "injury_type": injury_type,
                    "treatment": treatment_type,
                }
            )
            response.raise_for_status()
            result = response.json()

            criteria_met = result.get("criteria_met", [])
            criteria_not_met = result.get("criteria_not_met", [])
            reasoning = result.get("reasoning", "")
            citations = result.get("citations", [])

            citation_text = ", ".join(citations) if citations else "29 CFR 1904.7"

            response_parts = [
                f"**Information Provided:**",
                f"• Injury/Illness: {injury_type or 'Not specified'}",
                f"• Treatment: {treatment_type or 'Not specified'}",
                f"",
                f"**Regulatory Criteria ({citation_text}):**",
                f"{reasoning}",
            ]

            return "\n".join(response_parts)

    except Exception as e:
        _logger.error(f"Recordability Engine call failed: {e}")
        return (
            "I encountered an error retrieving regulatory criteria. "
            "Please provide more details about the injury and treatment, "
            "and I'll have the full team evaluate your question."
        )


def FirstAidVsMedical(entities: list[dict]) -> str:
    """
    Handle first aid vs medical treatment questions.
    Searches eCFR for 29 CFR 1904.7(a) definitions.
    """
    treatment_type = get_treatment_type(entities)

    try:
        # Search eCFR for first aid definition
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{ECFR_URL}/search",
                json={
                    "query": f"first aid medical treatment {treatment_type or ''}".strip(),
                    "top_k": 3,
                }
            )
            response.raise_for_status()
            results = response.json().get("results", [])

            if results:
                top_result = results[0]
                return (
                    f"Per 29 CFR 1904.7(a), OSHA defines specific treatments as first aid. "
                    f"{top_result.get('text', '')} "
                    f"See {top_result.get('citation', '29 CFR 1904.7(a)')}."
                )
            else:
                return (
                    "First aid treatments are specifically listed in 29 CFR 1904.7(a) and include: "
                    "non-prescription medications at non-prescription strength, tetanus shots, "
                    "wound coverings, hot/cold therapy, non-rigid supports, and similar minor treatments. "
                    "Medical treatment is anything beyond this list."
                )

    except Exception as e:
        _logger.error(f"eCFR search failed: {e}")
        return (
            "First aid is specifically defined in 29 CFR 1904.7(a). Generally, first aid includes "
            "minor treatments like bandages, non-prescription medications, and cleaning wounds. "
            "Medical treatment includes stitches, prescription medications, and physical therapy."
        )


def DaysAwayCalculation(entities: list[dict]) -> str:
    """
    Handle days away from work calculation questions.
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{ECFR_URL}/search",
                json={
                    "query": "days away from work counting calendar",
                    "top_k": 2,
                }
            )
            response.raise_for_status()
            results = response.json().get("results", [])

            if results:
                return (
                    f"Per 29 CFR 1904.7(b)(3): {results[0].get('text', '')} "
                    "Key points: Do NOT count the day of injury. "
                    "DO count all calendar days including weekends and holidays. "
                    "Cap at 180 days maximum."
                )

    except Exception as e:
        _logger.error(f"eCFR search failed: {e}")

    return (
        "Per 29 CFR 1904.7(b)(3), when counting days away from work: "
        "(1) Do NOT count the day of injury or illness onset. "
        "(2) Count all calendar days, including weekends, holidays, and days the employee wouldn't normally work. "
        "(3) Stop counting at 180 days. "
        "(4) If the employee leaves employment for unrelated reasons, stop counting."
    )


def IndustryRiskProfile(entities: list[dict]) -> str:
    """
    Handle industry risk profile questions.
    Routes to Analytics API for BLS data.
    """
    naics_code = get_naics_code(entities)

    if not naics_code:
        return (
            "To provide industry risk data, I need your NAICS code. "
            "This is typically a 4-6 digit code identifying your industry. "
            "You can find it on your business tax documents or search at census.gov/naics."
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{ANALYTICS_URL}/risk-profile/{naics_code}"
            )
            response.raise_for_status()
            data = response.json()

            industry_name = data.get("industry_name", "your industry")
            tcir = data.get("tcir", "N/A")
            dart = data.get("dart", "N/A")
            risk_level = data.get("risk_level", "unknown")
            year = data.get("year", "recent")

            return (
                f"**Industry Risk Profile for NAICS {naics_code}** ({industry_name}):\n\n"
                f"• Total Case Incidence Rate (TCIR): {tcir} per 100 FTE\n"
                f"• Days Away/Restricted/Transfer (DART): {dart} per 100 FTE\n"
                f"• Risk Level: {risk_level}\n"
                f"• Data Year: {year}\n\n"
                f"Source: Bureau of Labor Statistics"
            )

    except Exception as e:
        _logger.error(f"Analytics API call failed: {e}")
        return (
            f"I couldn't retrieve data for NAICS {naics_code}. "
            "Please verify the code is correct, or I can have the Analytics team "
            "look up your industry data."
        )


def FormGeneration(entities: list[dict]) -> str:
    """
    Handle form generation requests.
    Note: Actual form generation requires Zone 2 access with authentication.
    """
    form_type = get_form_type(entities)

    if form_type:
        form_type_clean = form_type.lower().replace("form ", "").replace("osha ", "")
        if "300a" in form_type_clean:
            return (
                "To generate Form 300A (Annual Summary), I'll need access to your recorded incidents "
                "for the calendar year. Form 300A must be posted February 1 through April 30. "
                "Please confirm the year and I'll prepare the summary."
            )
        elif "301" in form_type_clean:
            return (
                "Form 301 (Injury and Illness Incident Report) is completed for each recordable case. "
                "I'll need the specific incident details. Which incident would you like to document?"
            )
        elif "300" in form_type_clean:
            return (
                "Form 300 (Log of Work-Related Injuries and Illnesses) tracks all recordable cases. "
                "To add an entry or generate the log, please specify which incidents to include."
            )

    return (
        "I can help with OSHA forms:\n\n"
        "• **Form 300**: Log of Work-Related Injuries and Illnesses\n"
        "• **Form 300A**: Annual Summary (post Feb 1 - Apr 30)\n"
        "• **Form 301**: Individual Incident Report\n\n"
        "Which form do you need?"
    )


def DefinitionLookup(entities: list[dict]) -> str:
    """
    Handle regulatory definition lookups.
    Searches eCFR for specific terms.
    """
    # Try to extract what term they're looking for from entities
    search_term = None
    for ent in entities:
        if ent.get("category") in ["TreatmentType", "InjuryType"]:
            search_term = ent.get("text")
            break

    if not search_term:
        return (
            "I can look up OSHA recordkeeping definitions. "
            "What term would you like me to define? "
            "Common lookups include: recordable, work-related, first aid, medical treatment, "
            "days away, restricted work, and privacy case."
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{ECFR_URL}/search",
                json={
                    "query": f"definition {search_term}",
                    "top_k": 2,
                }
            )
            response.raise_for_status()
            results = response.json().get("results", [])

            if results:
                top = results[0]
                return (
                    f"**{search_term}** - {top.get('text', 'Definition not found.')} "
                    f"See {top.get('citation', '29 CFR 1904')}."
                )

    except Exception as e:
        _logger.error(f"eCFR search failed: {e}")

    return (
        f"I couldn't find a specific definition for '{search_term}' in the regulations. "
        "Let me route this to the Governance team for a more thorough search."
    )
