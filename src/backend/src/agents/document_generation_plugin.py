# Copyright (c) Sagevia - IRIS Symphony OSHA
"""
Document Generation Plugin - IRI Experience Domain (🤝)
======================================================
Generates OSHA forms (300, 300A, 301) via the Zone 2 Documents API.

Capabilities:
- Generate Form 300 (Log of Injuries)
- Generate Form 300A (Annual Summary)
- Generate Form 301 (Incident Report)
- PDF creation and retrieval
"""

import os
import httpx
from typing import Annotated, Optional
from semantic_kernel.functions import kernel_function


class DocumentGenerationPlugin:
    """Plugin for IRI Experience domain - OSHA form generation."""
    
    def __init__(self):
        """Initialize the Document Generation plugin."""
        self.documents_api_url = os.environ.get(
            "IRIS_ZONE2_DOCUMENTS_URL",
            "https://ca-svo-documents-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io"
        )
        self.auth_token = os.environ.get("IRIS_AUTH_TOKEN", "")
    
    @kernel_function(
        name="generate_form_300",
        description="Generate OSHA Form 300 (Log of Work-Related Injuries and Illnesses) for a year."
    )
    def generate_form_300(
        self,
        year: Annotated[int, "The calendar year for the log"],
        establishment_name: Annotated[str, "Name of the establishment"],
        include_privacy_cases: Annotated[bool, "Include privacy cases (as 'Privacy Case')"] = True
    ) -> str:
        """
        Generate Form 300 for a calendar year.
        
        Args:
            year: Calendar year
            establishment_name: Establishment name
            include_privacy_cases: Include privacy cases
            
        Returns:
            Form generation confirmation or link
        """
        try:
            response = httpx.post(
                f"{self.documents_api_url}/forms/300",
                json={
                    "year": year,
                    "establishment_name": establishment_name,
                    "include_privacy_cases": include_privacy_cases
                },
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            
            return (
                f"✅ Form 300 Generated Successfully\n"
                f"{'=' * 50}\n"
                f"Year: {year}\n"
                f"Establishment: {establishment_name}\n"
                f"Total Cases: {result.get('total_cases', 0)}\n"
                f"Privacy Cases: {result.get('privacy_cases', 0)}\n"
                f"Document ID: {result.get('document_id')}\n"
                f"Download URL: {result.get('download_url', 'Pending')}\n\n"
                f"Note: Form 300 must be kept on file for 5 years."
            )
            
        except Exception as e:
            return self._simulate_form_300(year, establishment_name)
    
    @kernel_function(
        name="generate_form_300a",
        description="Generate OSHA Form 300A (Summary of Work-Related Injuries and Illnesses) for annual posting."
    )
    def generate_form_300a(
        self,
        year: Annotated[int, "The calendar year for the summary"],
        establishment_name: Annotated[str, "Name of the establishment"],
        naics_code: Annotated[str, "NAICS code for the establishment"],
        annual_average_employees: Annotated[int, "Annual average number of employees"],
        total_hours_worked: Annotated[int, "Total hours worked by all employees"]
    ) -> str:
        """
        Generate Form 300A annual summary.
        
        Args:
            year: Calendar year
            establishment_name: Establishment name
            naics_code: Industry NAICS code
            annual_average_employees: Average employee count
            total_hours_worked: Total hours worked
            
        Returns:
            Form generation confirmation
        """
        try:
            response = httpx.post(
                f"{self.documents_api_url}/forms/300a",
                json={
                    "year": year,
                    "establishment_name": establishment_name,
                    "naics_code": naics_code,
                    "annual_average_employees": annual_average_employees,
                    "total_hours_worked": total_hours_worked
                },
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            
            return (
                f"✅ Form 300A Generated Successfully\n"
                f"{'=' * 50}\n"
                f"Year: {year}\n"
                f"Establishment: {establishment_name}\n"
                f"NAICS: {naics_code}\n"
                f"Average Employees: {annual_average_employees}\n"
                f"Total Hours: {total_hours_worked:,}\n\n"
                f"Summary Totals:\n"
                f"  Total Deaths: {result.get('deaths', 0)}\n"
                f"  Days Away Cases: {result.get('days_away_cases', 0)}\n"
                f"  Days Away: {result.get('total_days_away', 0)}\n"
                f"  Job Transfer/Restriction Cases: {result.get('transfer_cases', 0)}\n"
                f"  Other Recordable Cases: {result.get('other_cases', 0)}\n\n"
                f"Document ID: {result.get('document_id')}\n"
                f"Download URL: {result.get('download_url', 'Pending')}\n\n"
                f"⚠️ POSTING REQUIREMENT:\n"
                f"Post Form 300A from February 1 through April 30 of {year + 1}\n"
                f"in a visible location where employee notices are posted."
            )
            
        except Exception as e:
            return self._simulate_form_300a(
                year, establishment_name, naics_code,
                annual_average_employees, total_hours_worked
            )
    
    @kernel_function(
        name="generate_form_301",
        description="Generate OSHA Form 301 (Injury and Illness Incident Report) for a specific case."
    )
    def generate_form_301(
        self,
        incident_id: Annotated[str, "The incident ID to generate Form 301 for"]
    ) -> str:
        """
        Generate Form 301 for a specific incident.
        
        Args:
            incident_id: ID of the incident
            
        Returns:
            Form generation confirmation
        """
        try:
            response = httpx.post(
                f"{self.documents_api_url}/forms/301",
                json={"incident_id": incident_id},
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            
            return (
                f"✅ Form 301 Generated Successfully\n"
                f"{'=' * 50}\n"
                f"Incident ID: {incident_id}\n"
                f"Employee: {result.get('employee_name', '[See form]')}\n"
                f"Date of Injury: {result.get('incident_date')}\n"
                f"Document ID: {result.get('document_id')}\n"
                f"Download URL: {result.get('download_url', 'Pending')}\n\n"
                f"Note: Form 301 must be completed within 7 calendar days "
                f"of receiving information that a recordable case occurred.\n"
                f"Keep form on file for 5 years."
            )
            
        except Exception as e:
            return (
                f"[SIMULATION] Form 301 Generation\n"
                f"{'=' * 50}\n"
                f"Incident ID: {incident_id}\n"
                f"Status: Would be generated when Zone 2 API is available\n\n"
                f"Form 301 Requirements:\n"
                f"• Complete within 7 days of learning about recordable case\n"
                f"• Include all injury details and circumstances\n"
                f"• Keep on file for 5 years\n"
                f"• May substitute workers' comp form if equivalent"
            )
    
    @kernel_function(
        name="get_posting_requirements",
        description="Get current OSHA form posting requirements and deadlines."
    )
    def get_posting_requirements(
        self,
        current_date: Annotated[Optional[str], "Current date (YYYY-MM-DD) for deadline calculation"] = None
    ) -> str:
        """
        Get posting requirements and deadlines.
        
        Args:
            current_date: Current date for calculation
            
        Returns:
            Posting requirements and deadlines
        """
        from datetime import datetime, date
        
        if current_date:
            today = datetime.strptime(current_date, "%Y-%m-%d").date()
        else:
            today = date.today()
        
        current_year = today.year
        
        # Form 300A posting period
        posting_start = date(current_year, 2, 1)
        posting_end = date(current_year, 4, 30)
        
        # Electronic submission deadline
        electronic_deadline = date(current_year, 3, 2)
        
        # Determine status
        if today < posting_start:
            posting_status = f"⏳ Posting begins February 1, {current_year}"
            days_until = (posting_start - today).days
            posting_status += f" ({days_until} days away)"
        elif today <= posting_end:
            posting_status = f"📋 CURRENTLY IN POSTING PERIOD - Must be posted until April 30"
            days_remaining = (posting_end - today).days
            posting_status += f" ({days_remaining} days remaining)"
        else:
            posting_status = f"✅ Posting period ended April 30, {current_year}"
        
        # Electronic submission status
        if today < electronic_deadline:
            electronic_status = f"⏳ Due by March 2, {current_year}"
            if (electronic_deadline - today).days <= 30:
                electronic_status += f" ⚠️ ({(electronic_deadline - today).days} days remaining)"
        else:
            electronic_status = f"✅ Deadline passed (March 2, {current_year})"
        
        return (
            f"OSHA Recordkeeping Requirements ({current_year})\n"
            f"{'=' * 50}\n\n"
            f"📋 FORM 300A POSTING\n"
            f"   Period: February 1 - April 30, {current_year}\n"
            f"   For: Calendar year {current_year - 1} data\n"
            f"   Status: {posting_status}\n"
            f"   Location: Where employee notices are normally posted\n"
            f"   Certification: Must be certified by company executive\n\n"
            f"💻 ELECTRONIC SUBMISSION (ITA)\n"
            f"   Deadline: March 2, {current_year}\n"
            f"   Status: {electronic_status}\n"
            f"   Required for:\n"
            f"   • Establishments with 250+ employees (Form 300A)\n"
            f"   • Establishments with 20-249 employees in high-hazard industries\n"
            f"     (Forms 300A, 300, and 301)\n"
            f"   Submit at: https://www.osha.gov/injuryreporting\n\n"
            f"📁 RECORD RETENTION\n"
            f"   Forms 300, 300A, 301: Keep for 5 years following the year\n"
            f"   Current retention: {current_year - 5} through {current_year - 1} records"
        )
    
    def _simulate_form_300(self, year: int, establishment_name: str) -> str:
        """Simulate Form 300 generation."""
        return (
            f"[SIMULATION] Form 300 Generation\n"
            f"{'=' * 50}\n"
            f"Year: {year}\n"
            f"Establishment: {establishment_name}\n\n"
            f"When Zone 2 Documents API is available, this will:\n"
            f"• Compile all {year} incidents into Form 300 log\n"
            f"• Replace employee names with 'Privacy Case' where applicable\n"
            f"• Generate downloadable PDF\n\n"
            f"Form 300 Columns:\n"
            f"A - Case No. | B - Employee Name | C - Job Title\n"
            f"D - Date | E - Location | F - Description\n"
            f"G-J - Classify Case | K-L - Days Away/Restricted"
        )
    
    def _simulate_form_300a(
        self, year: int, establishment_name: str, naics_code: str,
        annual_average_employees: int, total_hours_worked: int
    ) -> str:
        """Simulate Form 300A generation."""
        return (
            f"[SIMULATION] Form 300A Generation\n"
            f"{'=' * 50}\n"
            f"Year: {year}\n"
            f"Establishment: {establishment_name}\n"
            f"NAICS: {naics_code}\n"
            f"Average Employees: {annual_average_employees}\n"
            f"Total Hours: {total_hours_worked:,}\n\n"
            f"When Zone 2 Documents API is available, this will:\n"
            f"• Calculate summary totals from Form 300\n"
            f"• Compute incidence rates\n"
            f"• Generate certification-ready PDF\n\n"
            f"⚠️ REMINDER:\n"
            f"Post from February 1 - April 30 of {year + 1}\n"
            f"Must be certified by company executive"
        )
