# Copyright (c) Sagevia - IRIS Symphony OSHA
"""
Incident Management Plugin - IRI Experience Domain (🤝)
======================================================
Manages incident records via the Zone 2 Incidents API (PII-protected).

Capabilities:
- Create new incident records
- Update existing incidents
- Track days away/restricted work
- Handle privacy concern cases
"""

import os
import httpx
from typing import Annotated, Optional
from semantic_kernel.functions import kernel_function


class IncidentManagementPlugin:
    """Plugin for IRI Experience domain - Zone 2 incident management."""
    
    def __init__(self):
        """Initialize the Incident Management plugin."""
        self.incidents_api_url = os.environ.get(
            "IRIS_ZONE2_INCIDENTS_URL",
            "https://ca-svo-incidents-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io"
        )
        self.auth_token = os.environ.get("IRIS_AUTH_TOKEN", "")
    
    @kernel_function(
        name="create_incident",
        description="Create a new incident record in the Zone 2 database."
    )
    def create_incident(
        self,
        employee_name: Annotated[str, "Employee's name (protected by RLS)"],
        incident_date: Annotated[str, "Date of incident (YYYY-MM-DD)"],
        injury_description: Annotated[str, "Description of the injury or illness"],
        body_part: Annotated[str, "Body part affected"],
        incident_location: Annotated[str, "Where the incident occurred"],
        is_privacy_case: Annotated[bool, "Whether this is a privacy concern case"] = False
    ) -> str:
        """
        Create a new incident record.
        
        Args:
            employee_name: Name of injured employee
            incident_date: Date of incident
            injury_description: What happened
            body_part: Body part affected
            incident_location: Location
            is_privacy_case: Privacy concern flag
            
        Returns:
            Confirmation with incident ID
        """
        try:
            response = httpx.post(
                f"{self.incidents_api_url}/incidents",
                json={
                    "employee_name": employee_name,
                    "incident_date": incident_date,
                    "injury_description": injury_description,
                    "body_part": body_part,
                    "incident_location": incident_location,
                    "is_privacy_case": is_privacy_case,
                    "status": "open"
                },
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            privacy_note = ""
            if is_privacy_case:
                privacy_note = (
                    "\n\n⚠️ PRIVACY CASE: Per 29 CFR 1904.29, this case will be recorded as "
                    "'Privacy Case' on Form 300 instead of the employee's name."
                )
            
            return (
                f"✅ Incident Created Successfully\n"
                f"{'=' * 50}\n"
                f"Incident ID: {result.get('incident_id')}\n"
                f"Employee: {employee_name}\n"
                f"Date: {incident_date}\n"
                f"Description: {injury_description}\n"
                f"Body Part: {body_part}\n"
                f"Location: {incident_location}\n"
                f"Status: Open"
                f"{privacy_note}"
            )
            
        except httpx.RequestError as e:
            return self._simulate_create(
                employee_name, incident_date, injury_description, 
                body_part, incident_location, is_privacy_case
            )
        except Exception as e:
            return f"Error creating incident: {str(e)}"
    
    @kernel_function(
        name="update_incident",
        description="Update an existing incident record with new information."
    )
    def update_incident(
        self,
        incident_id: Annotated[str, "The incident ID to update"],
        days_away: Annotated[Optional[int], "Number of days away from work"] = None,
        days_restricted: Annotated[Optional[int], "Number of days on restricted work"] = None,
        days_transfer: Annotated[Optional[int], "Number of days on job transfer"] = None,
        case_closed: Annotated[bool, "Whether to close the case"] = False,
        notes: Annotated[Optional[str], "Additional notes"] = None
    ) -> str:
        """
        Update an existing incident.
        
        Args:
            incident_id: ID of the incident to update
            days_away: Days away from work
            days_restricted: Days on restricted work
            days_transfer: Days on job transfer
            case_closed: Close the case
            notes: Additional notes
            
        Returns:
            Update confirmation
        """
        try:
            update_data = {"incident_id": incident_id}
            
            if days_away is not None:
                update_data["days_away"] = min(days_away, 180)  # Cap at 180
            if days_restricted is not None:
                update_data["days_restricted"] = min(days_restricted, 180)
            if days_transfer is not None:
                update_data["days_transfer"] = min(days_transfer, 180)
            if case_closed:
                update_data["status"] = "closed"
            if notes:
                update_data["notes"] = notes
            
            response = httpx.patch(
                f"{self.incidents_api_url}/incidents/{incident_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            return (
                f"✅ Incident Updated Successfully\n"
                f"{'=' * 50}\n"
                f"Incident ID: {incident_id}\n"
                f"Days Away: {days_away or 'N/A'}\n"
                f"Days Restricted: {days_restricted or 'N/A'}\n"
                f"Days Transfer: {days_transfer or 'N/A'}\n"
                f"Status: {'Closed' if case_closed else 'Open'}\n"
                f"Notes: {notes or 'None'}"
            )
            
        except httpx.RequestError:
            return (
                f"[SIMULATION] Incident {incident_id} would be updated:\n"
                f"- Days Away: {days_away}\n"
                f"- Days Restricted: {days_restricted}\n"
                f"- Status: {'Closed' if case_closed else 'Open'}"
            )
        except Exception as e:
            return f"Error updating incident: {str(e)}"
    
    @kernel_function(
        name="get_incident",
        description="Retrieve details of an existing incident."
    )
    def get_incident(
        self,
        incident_id: Annotated[str, "The incident ID to retrieve"]
    ) -> str:
        """
        Get incident details.
        
        Args:
            incident_id: ID of the incident
            
        Returns:
            Incident details
        """
        try:
            response = httpx.get(
                f"{self.incidents_api_url}/incidents/{incident_id}",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            return (
                f"Incident Details\n"
                f"{'=' * 50}\n"
                f"ID: {result.get('incident_id')}\n"
                f"Employee: {result.get('employee_name')}\n"
                f"Date: {result.get('incident_date')}\n"
                f"Description: {result.get('injury_description')}\n"
                f"Body Part: {result.get('body_part')}\n"
                f"Location: {result.get('incident_location')}\n"
                f"Days Away: {result.get('days_away', 0)}\n"
                f"Days Restricted: {result.get('days_restricted', 0)}\n"
                f"Privacy Case: {result.get('is_privacy_case', False)}\n"
                f"Status: {result.get('status')}"
            )
            
        except Exception as e:
            return f"Error retrieving incident {incident_id}: {str(e)}"
    
    @kernel_function(
        name="check_privacy_criteria",
        description="Determine if a case qualifies as a privacy concern case per 29 CFR 1904.29."
    )
    def check_privacy_criteria(
        self,
        injury_type: Annotated[str, "Type of injury or illness"],
        body_part: Annotated[str, "Body part affected"],
        circumstances: Annotated[str, "Circumstances of the injury"]
    ) -> str:
        """
        Check if a case meets privacy concern criteria.
        
        Args:
            injury_type: Type of injury
            body_part: Body part affected
            circumstances: How it happened
            
        Returns:
            Privacy determination with explanation
        """
        privacy_triggers = {
            "intimate_body_part": [
                "groin", "genitals", "genital", "breast", "buttock", 
                "reproductive", "sexual organ"
            ],
            "sexual_assault": [
                "sexual assault", "rape", "harassment", "inappropriate touching"
            ],
            "mental_illness": [
                "mental illness", "psychiatric", "depression", "anxiety disorder",
                "ptsd", "psychological"
            ],
            "hiv_hepatitis_tb": [
                "hiv", "hepatitis", "tuberculosis", "tb", "aids"
            ],
            "needlestick": [
                "needlestick", "sharps", "bloodborne", "blood exposure"
            ]
        }
        
        combined_text = f"{injury_type} {body_part} {circumstances}".lower()
        
        matches = []
        for category, keywords in privacy_triggers.items():
            for keyword in keywords:
                if keyword in combined_text:
                    matches.append(category.replace("_", " ").title())
                    break
        
        if matches:
            return (
                f"⚠️ PRIVACY CONCERN CASE IDENTIFIED\n"
                f"{'=' * 50}\n"
                f"Per 29 CFR 1904.29(b)(7), this case qualifies as a privacy concern.\n\n"
                f"Matching criteria: {', '.join(matches)}\n\n"
                f"Required actions:\n"
                f"• Enter 'Privacy Case' in Column B of Form 300 (instead of name)\n"
                f"• Keep a separate, confidential list linking case numbers to names\n"
                f"• Employee may request name be withheld from Form 300\n\n"
                f"Privacy concern cases include:\n"
                f"1. Injury to intimate body part or reproductive system\n"
                f"2. Sexual assault\n"
                f"3. Mental illness\n"
                f"4. HIV, hepatitis, or tuberculosis\n"
                f"5. Needlestick or sharps injury with blood/OPIM exposure\n"
                f"6. Any case where employee requests privacy"
            )
        else:
            return (
                f"✅ NOT A PRIVACY CONCERN CASE\n"
                f"{'=' * 50}\n"
                f"Based on the information provided, this case does not meet the "
                f"privacy concern criteria under 29 CFR 1904.29(b)(7).\n\n"
                f"The employee's name should be recorded on Form 300.\n\n"
                f"Note: The employee may still request their name be withheld "
                f"(voluntary privacy request)."
            )
    
    def _simulate_create(
        self, employee_name, incident_date, injury_description,
        body_part, incident_location, is_privacy_case
    ) -> str:
        """Simulate incident creation when API unavailable."""
        import uuid
        fake_id = str(uuid.uuid4())[:8]
        
        privacy_note = ""
        if is_privacy_case:
            privacy_note = "\n\n⚠️ PRIVACY CASE flagged per 29 CFR 1904.29"
        
        return (
            f"[SIMULATION] Incident Created\n"
            f"{'=' * 50}\n"
            f"Incident ID: INC-{fake_id}\n"
            f"Employee: {employee_name}\n"
            f"Date: {incident_date}\n"
            f"Description: {injury_description}\n"
            f"Body Part: {body_part}\n"
            f"Location: {incident_location}\n"
            f"Status: Open"
            f"{privacy_note}\n\n"
            f"Note: Zone 2 API unavailable. This is a simulated response."
        )
