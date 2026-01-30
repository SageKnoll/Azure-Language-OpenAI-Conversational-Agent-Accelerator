# Copyright (c) Sagevia - IRIS Symphony OSHA
"""
Recordability Plugin - IRI Governance Domain (⚖️)
=================================================
Applies Q0-Q4 recordability decision logic via the Zone 1 Recordability Engine.

Decision Framework:
- Q0: Is there an injury or illness?
- Q1: Is it work-related?
- Q2: Is it a new case?
- Q3: Does it meet general recording criteria?
- Q4: Are there any exemptions?
"""

import os
import httpx
from typing import Annotated, Optional
from semantic_kernel.functions import kernel_function


class RecordabilityPlugin:
    """Plugin for OSHA recordability determinations using Q0-Q4 logic."""
    
    def __init__(self):
        """Initialize the Recordability plugin."""
        self.recordability_api_url = os.environ.get(
            "IRIS_ZONE1_RECORDABILITY_URL",
            "https://ca-svo-recordability-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io"
        )
    
    @kernel_function(
        name="evaluate_recordability",
        description="Evaluate whether a case meets OSHA recordability criteria using Q0-Q4 decision logic."
    )
    def evaluate_recordability(
        self,
        injury_description: Annotated[str, "Description of the injury or illness"],
        treatment_provided: Annotated[str, "Treatment provided (e.g., 'stitches', 'bandage', 'prescription medication')"],
        work_related: Annotated[bool, "Whether the injury occurred in the work environment"],
        days_away: Annotated[Optional[int], "Number of days away from work (if any)"] = None,
        restricted_work: Annotated[bool, "Whether work was restricted"] = False
    ) -> str:
        """
        Evaluate recordability using the Q0-Q4 framework.
        
        Args:
            injury_description: What happened
            treatment_provided: What treatment was given
            work_related: Did it occur at work
            days_away: Days away from work
            restricted_work: Was work restricted
            
        Returns:
            Recordability assessment with criteria met/not met
        """
        try:
            # Call Zone 1 Recordability Engine
            response = httpx.post(
                f"{self.recordability_api_url}/evaluate",
                json={
                    "injury_description": injury_description,
                    "treatment_provided": treatment_provided,
                    "work_related": work_related,
                    "days_away": days_away,
                    "restricted_work": restricted_work
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return self._format_evaluation(result)
            
        except Exception as e:
            # Fallback to local evaluation
            return self._local_evaluate(
                injury_description, treatment_provided, work_related, days_away, restricted_work
            )
    
    @kernel_function(
        name="check_first_aid_list",
        description="Check if a treatment is on the OSHA first aid list (not recordable)."
    )
    def check_first_aid_list(
        self,
        treatment: Annotated[str, "The treatment to check (e.g., 'bandage', 'stitches', 'ibuprofen')"]
    ) -> str:
        """
        Check if a treatment qualifies as first aid per 29 CFR 1904.7(a).
        
        Args:
            treatment: The treatment to check
            
        Returns:
            Whether treatment is first aid or medical treatment
        """
        first_aid_list = [
            "bandage", "band-aid", "butterfly closure", "steri-strip",
            "finger guard", "splint", "elastic bandage", "wrap",
            "non-prescription medication", "aspirin", "ibuprofen", "acetaminophen",
            "antibiotic ointment", "antiseptic", "eye wash", "eye flush",
            "tetanus shot", "tetanus immunization",
            "wound cleaning", "soaking", "irrigation",
            "hot pack", "cold pack", "ice", "heat therapy",
            "massage", "drinking fluids", "oxygen",
            "drilling fingernail", "toenail", "draining blister",
            "eye patch", "rigid stay", "finger splint"
        ]
        
        medical_treatment_list = [
            "stitches", "sutures", "staples",
            "prescription medication", "prescription strength",
            "physical therapy", "chiropractic",
            "surgery", "surgical",
            "cast", "rigid immobilization",
            "root canal", "tooth extraction",
            "mri", "ct scan", "x-ray with finding"
        ]
        
        treatment_lower = treatment.lower()
        
        # Check first aid list
        for fa in first_aid_list:
            if fa in treatment_lower:
                return (
                    f"'{treatment}' IS on the first aid list per 29 CFR 1904.7(a).\n"
                    f"First aid treatments do NOT make a case recordable by themselves.\n"
                    f"However, check other recording criteria (days away, restricted work, etc.)."
                )
        
        # Check medical treatment list
        for mt in medical_treatment_list:
            if mt in treatment_lower:
                return (
                    f"'{treatment}' is MEDICAL TREATMENT beyond first aid.\n"
                    f"Per 29 CFR 1904.7(a), this treatment MEETS the recording criteria.\n"
                    f"If the case is work-related and a new case, it should be recorded."
                )
        
        return (
            f"'{treatment}' is not definitively on either list.\n"
            f"Consider: Is this treatment beyond what a non-medical person could administer?\n"
            f"If administered by a physician AND goes beyond the first aid list, it's likely recordable."
        )
    
    @kernel_function(
        name="calculate_days_away",
        description="Calculate the number of days away from work for OSHA recording."
    )
    def calculate_days_away(
        self,
        injury_date: Annotated[str, "Date of injury (YYYY-MM-DD)"],
        return_date: Annotated[str, "Date employee returned to work (YYYY-MM-DD)"],
        include_weekends: Annotated[bool, "Whether to include weekends in count"] = True
    ) -> str:
        """
        Calculate days away from work per 29 CFR 1904.7(b)(3).
        
        Args:
            injury_date: When the injury occurred
            return_date: When employee returned
            include_weekends: Include weekends/holidays
            
        Returns:
            Calculated days away with explanation
        """
        from datetime import datetime, timedelta
        
        try:
            injury = datetime.strptime(injury_date, "%Y-%m-%d")
            return_dt = datetime.strptime(return_date, "%Y-%m-%d")
            
            # Don't count day of injury
            start_count = injury + timedelta(days=1)
            
            if include_weekends:
                # Calendar days
                days = (return_dt - start_count).days
            else:
                # Business days only (not standard OSHA method)
                days = 0
                current = start_count
                while current < return_dt:
                    if current.weekday() < 5:  # Mon-Fri
                        days += 1
                    current += timedelta(days=1)
            
            # Cap at 180 days
            capped = min(days, 180)
            
            result = (
                f"Days Away Calculation per 29 CFR 1904.7(b)(3):\n"
                f"- Injury date: {injury_date}\n"
                f"- Return date: {return_date}\n"
                f"- Days counted: {days}\n"
            )
            
            if days > 180:
                result += f"- Capped at: 180 days (maximum per OSHA)\n"
            
            result += (
                f"\nNote: Do not count the day of injury. "
                f"Count calendar days (including weekends/holidays) if employee "
                f"would not have been able to work those days."
            )
            
            return result
            
        except ValueError as e:
            return f"Error parsing dates: {e}. Use YYYY-MM-DD format."
    
    def _local_evaluate(
        self,
        injury_description: str,
        treatment_provided: str,
        work_related: bool,
        days_away: Optional[int],
        restricted_work: bool
    ) -> str:
        """Local fallback evaluation when API is unavailable."""
        
        results = {
            "Q0": {"met": True, "reason": f"Injury/illness described: {injury_description}"},
            "Q1": {"met": work_related, "reason": "Work-related" if work_related else "Not work-related"},
            "Q2": {"met": True, "reason": "Assumed new case (no prior history provided)"},
            "Q3": {"met": False, "reason": "Checking criteria..."},
            "Q4": {"met": False, "reason": "No exemptions identified"}
        }
        
        # Check Q3 criteria
        q3_criteria = []
        
        # Medical treatment beyond first aid
        fa_check = self.check_first_aid_list(treatment_provided)
        if "MEDICAL TREATMENT" in fa_check:
            q3_criteria.append("Medical treatment beyond first aid")
            results["Q3"]["met"] = True
        
        # Days away
        if days_away and days_away > 0:
            q3_criteria.append(f"Days away from work: {days_away}")
            results["Q3"]["met"] = True
        
        # Restricted work
        if restricted_work:
            q3_criteria.append("Restricted work or job transfer")
            results["Q3"]["met"] = True
        
        results["Q3"]["reason"] = ", ".join(q3_criteria) if q3_criteria else "No recording criteria met"
        
        # Format output
        output = "RECORDABILITY EVALUATION (Q0-Q4 Framework)\n" + "=" * 50 + "\n\n"
        
        for q, data in results.items():
            status = "✓ MET" if data["met"] else "✗ NOT MET"
            output += f"{q}: {status}\n    {data['reason']}\n\n"
        
        # Final determination
        all_met = results["Q0"]["met"] and results["Q1"]["met"] and results["Q2"]["met"] and results["Q3"]["met"]
        
        if all_met and not results["Q4"]["met"]:
            output += (
                "=" * 50 + "\n"
                "ASSESSMENT: This case MEETS the recording criteria.\n"
                "Per 29 CFR 1904.7, cases meeting these criteria should be recorded.\n"
                "Note: This is regulatory guidance, not a determination. "
                "The employer makes the final recording decision."
            )
        else:
            missing = [q for q, d in results.items() if not d["met"] and q != "Q4"]
            output += (
                "=" * 50 + "\n"
                f"ASSESSMENT: Recording criteria NOT fully met.\n"
                f"Missing: {', '.join(missing)}\n"
                "Review the case details to confirm."
            )
        
        return output
    
    def _format_evaluation(self, result: dict) -> str:
        """Format API evaluation result."""
        output = "RECORDABILITY EVALUATION (Q0-Q4 Framework)\n" + "=" * 50 + "\n\n"
        
        for q in ["Q0", "Q1", "Q2", "Q3", "Q4"]:
            if q in result:
                data = result[q]
                status = "✓ MET" if data.get("met") else "✗ NOT MET"
                output += f"{q}: {status}\n    {data.get('reason', '')}\n\n"
        
        output += "=" * 50 + "\n"
        output += f"ASSESSMENT: {result.get('assessment', 'See details above')}\n"
        
        return output
