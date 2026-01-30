# Copyright (c) Sagevia - IRIS Symphony OSHA
"""
Industry Analytics Plugin - IRI Analytics Domain (📊)
=====================================================
Provides industry risk data from BLS injury rates and NAICS codes.

Capabilities:
- NAICS code lookup and classification
- BLS injury and illness rates (TCIR, DART)
- Industry risk comparisons
- Benchmark calculations
"""

import os
import httpx
from typing import Annotated, Optional
from semantic_kernel.functions import kernel_function


class IndustryAnalyticsPlugin:
    """Plugin for IRI Analytics domain - BLS data, NAICS codes, industry risk."""
    
    def __init__(self):
        """Initialize the Industry Analytics plugin."""
        self.analytics_api_url = os.environ.get(
            "IRIS_ZONE1_ANALYTICS_URL",
            "https://ca-svo-analytics-dev.kindcliff-8012a32c.centralus.azurecontainerapps.io"
        )
    
    @kernel_function(
        name="get_industry_rates",
        description="Get BLS injury and illness rates for a specific NAICS code or industry."
    )
    def get_industry_rates(
        self,
        naics_code: Annotated[str, "The NAICS code (e.g., '238220' for plumbing contractors)"],
        year: Annotated[Optional[int], "Data year (defaults to most recent)"] = None
    ) -> str:
        """
        Retrieve BLS injury/illness rates for an industry.
        
        Args:
            naics_code: The NAICS classification code
            year: The year of data (optional)
            
        Returns:
            Industry injury rates with context
        """
        try:
            params = {"naics": naics_code}
            if year:
                params["year"] = year
                
            response = httpx.get(
                f"{self.analytics_api_url}/industry-rates",
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return self._format_rates(result)
            
        except Exception as e:
            return self._get_static_rates(naics_code)
    
    @kernel_function(
        name="lookup_naics",
        description="Look up NAICS code information by code or industry name."
    )
    def lookup_naics(
        self,
        query: Annotated[str, "NAICS code or industry name to look up"]
    ) -> str:
        """
        Look up NAICS classification information.
        
        Args:
            query: NAICS code or industry name
            
        Returns:
            NAICS classification details
        """
        try:
            response = httpx.get(
                f"{self.analytics_api_url}/naics/lookup",
                params={"q": query},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if not result:
                return f"No NAICS code found for '{query}'"
            
            return (
                f"NAICS Classification:\n"
                f"- Code: {result.get('code')}\n"
                f"- Title: {result.get('title')}\n"
                f"- Sector: {result.get('sector')}\n"
                f"- Description: {result.get('description', 'N/A')}"
            )
            
        except Exception as e:
            return self._get_static_naics(query)
    
    @kernel_function(
        name="compare_to_benchmark",
        description="Compare an employer's injury rate to industry benchmarks."
    )
    def compare_to_benchmark(
        self,
        employer_tcir: Annotated[float, "Employer's Total Case Incident Rate"],
        employer_dart: Annotated[float, "Employer's DART rate"],
        naics_code: Annotated[str, "NAICS code for comparison"]
    ) -> str:
        """
        Compare employer rates to industry benchmarks.
        
        Args:
            employer_tcir: Employer's TCIR (injuries per 100 FTE)
            employer_dart: Employer's DART rate
            naics_code: Industry NAICS code
            
        Returns:
            Comparison analysis
        """
        # Get industry rates
        industry_data = self._get_static_rates(naics_code)
        
        # Parse industry rates (simplified - would use API in production)
        industry_rates = {
            "238220": {"tcir": 2.8, "dart": 1.5, "name": "Plumbing, Heating, AC Contractors"},
            "236220": {"tcir": 3.2, "dart": 1.8, "name": "Commercial Building Construction"},
            "311": {"tcir": 4.1, "dart": 2.3, "name": "Food Manufacturing"},
            "622": {"tcir": 5.5, "dart": 2.9, "name": "Hospitals"},
        }
        
        # Find best match
        industry = None
        for code, data in industry_rates.items():
            if naics_code.startswith(code):
                industry = data
                break
        
        if not industry:
            return f"No benchmark data available for NAICS {naics_code}"
        
        # Calculate comparison
        tcir_ratio = employer_tcir / industry["tcir"] if industry["tcir"] > 0 else 0
        dart_ratio = employer_dart / industry["dart"] if industry["dart"] > 0 else 0
        
        tcir_status = "ABOVE" if tcir_ratio > 1.0 else "BELOW" if tcir_ratio < 1.0 else "AT"
        dart_status = "ABOVE" if dart_ratio > 1.0 else "BELOW" if dart_ratio < 1.0 else "AT"
        
        return (
            f"Industry Benchmark Comparison\n"
            f"{'=' * 50}\n"
            f"Industry: {industry['name']} (NAICS {naics_code})\n\n"
            f"TCIR (Total Case Incident Rate):\n"
            f"  - Employer: {employer_tcir:.2f}\n"
            f"  - Industry: {industry['tcir']:.2f}\n"
            f"  - Status: {tcir_status} benchmark ({tcir_ratio:.1%})\n\n"
            f"DART (Days Away, Restricted, Transfer):\n"
            f"  - Employer: {employer_dart:.2f}\n"
            f"  - Industry: {industry['dart']:.2f}\n"
            f"  - Status: {dart_status} benchmark ({dart_ratio:.1%})\n\n"
            f"Note: BLS data typically has a 2-year lag. "
            f"Rates are per 100 full-time equivalent workers."
        )
    
    @kernel_function(
        name="calculate_incidence_rate",
        description="Calculate OSHA incidence rates from raw numbers."
    )
    def calculate_incidence_rate(
        self,
        total_cases: Annotated[int, "Total number of recordable cases"],
        hours_worked: Annotated[int, "Total hours worked by all employees"],
        days_away_cases: Annotated[Optional[int], "Number of cases with days away"] = None
    ) -> str:
        """
        Calculate TCIR and DART rates.
        
        Args:
            total_cases: Number of OSHA recordable cases
            hours_worked: Total hours worked
            days_away_cases: Cases with days away/restricted/transfer
            
        Returns:
            Calculated incidence rates
        """
        # OSHA formula: (N × 200,000) / Hours worked
        # 200,000 = base for 100 full-time workers (40 hrs × 50 weeks)
        
        if hours_worked <= 0:
            return "Error: Hours worked must be greater than 0"
        
        tcir = (total_cases * 200000) / hours_worked
        
        result = (
            f"Incidence Rate Calculation\n"
            f"{'=' * 50}\n"
            f"Total Recordable Cases: {total_cases}\n"
            f"Total Hours Worked: {hours_worked:,}\n"
            f"Estimated FTEs: {hours_worked / 2000:.1f}\n\n"
            f"TCIR (Total Case Incident Rate): {tcir:.2f}\n"
            f"  Formula: ({total_cases} × 200,000) / {hours_worked:,}\n"
        )
        
        if days_away_cases is not None:
            dart = (days_away_cases * 200000) / hours_worked
            result += (
                f"\nDART Rate: {dart:.2f}\n"
                f"  Cases with days away/restricted/transfer: {days_away_cases}\n"
                f"  Formula: ({days_away_cases} × 200,000) / {hours_worked:,}\n"
            )
        
        result += (
            f"\nNote: Rates are per 100 full-time equivalent workers per year. "
            f"Compare to BLS industry averages for context."
        )
        
        return result
    
    def _format_rates(self, result: dict) -> str:
        """Format API rate results."""
        return (
            f"Industry Injury Rates (BLS Data)\n"
            f"{'=' * 50}\n"
            f"NAICS: {result.get('naics_code')}\n"
            f"Industry: {result.get('industry_name')}\n"
            f"Year: {result.get('year')}\n\n"
            f"Total Case Incident Rate (TCIR): {result.get('tcir', 'N/A')}\n"
            f"DART Rate: {result.get('dart', 'N/A')}\n"
            f"DAFWII Rate: {result.get('dafwii', 'N/A')}\n\n"
            f"Source: Bureau of Labor Statistics, Survey of Occupational Injuries and Illnesses"
        )
    
    def _get_static_rates(self, naics_code: str) -> str:
        """Fallback static rates when API unavailable."""
        rates = {
            "238220": {
                "name": "Plumbing, Heating, and Air-Conditioning Contractors",
                "tcir": 2.8, "dart": 1.5, "year": 2022
            },
            "236220": {
                "name": "Commercial and Institutional Building Construction",
                "tcir": 3.2, "dart": 1.8, "year": 2022
            },
            "311": {
                "name": "Food Manufacturing",
                "tcir": 4.1, "dart": 2.3, "year": 2022
            },
            "622": {
                "name": "Hospitals",
                "tcir": 5.5, "dart": 2.9, "year": 2022
            },
            "445": {
                "name": "Food and Beverage Stores",
                "tcir": 3.8, "dart": 1.9, "year": 2022
            },
            "23": {
                "name": "Construction (All)",
                "tcir": 2.8, "dart": 1.5, "year": 2022
            }
        }
        
        # Find best match
        for code, data in rates.items():
            if naics_code.startswith(code):
                return (
                    f"Industry Injury Rates (BLS Data)\n"
                    f"{'=' * 50}\n"
                    f"NAICS: {naics_code}\n"
                    f"Industry: {data['name']}\n"
                    f"Year: {data['year']}\n\n"
                    f"Total Case Incident Rate (TCIR): {data['tcir']}\n"
                    f"DART Rate: {data['dart']}\n\n"
                    f"Source: Bureau of Labor Statistics (cached data)\n"
                    f"Note: BLS data typically has a 2-year lag."
                )
        
        return f"No injury rate data available for NAICS {naics_code}. Check BLS.gov for current data."
    
    def _get_static_naics(self, query: str) -> str:
        """Fallback static NAICS lookup."""
        naics_data = {
            "238220": ("Plumbing, Heating, and Air-Conditioning Contractors", "Construction"),
            "236220": ("Commercial and Institutional Building Construction", "Construction"),
            "311": ("Food Manufacturing", "Manufacturing"),
            "622": ("Hospitals", "Health Care"),
            "445": ("Food and Beverage Stores", "Retail Trade"),
            "plumbing": ("238220 - Plumbing, Heating, and Air-Conditioning Contractors", "Construction"),
            "hospital": ("622 - Hospitals", "Health Care"),
            "construction": ("23 - Construction", "Construction"),
        }
        
        query_lower = query.lower()
        for key, (title, sector) in naics_data.items():
            if key in query_lower or query_lower in key:
                return f"NAICS Classification:\n- Code/Title: {title}\n- Sector: {sector}"
        
        return f"No NAICS data found for '{query}'. Search at census.gov/naics"
