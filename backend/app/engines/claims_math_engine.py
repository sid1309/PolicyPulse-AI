from datetime import datetime
from typing import Dict, Any, List
from backend.app.core.models import ClaimsAssessmentRequest, ClaimsAssessmentResult, CitationItem
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.engines.citation_linker import CitationLinker

class ClaimsMathEngine:
    """
    Evaluates claim eligibility, computes proportional room rent penalties, 
    calculates out-of-pocket deductions, and generates actionable document checklists.
    """

    def __init__(self, hybrid_retriever: HybridRetriever):
        self.retriever = hybrid_retriever

    def assess_claim(self, request: ClaimsAssessmentRequest) -> ClaimsAssessmentResult:
        # 1. Retrieve policy rules for treatment and room rent
        treatment_hits = self.retriever.retrieve(
            query=f"{request.treatment_name} waiting period coverage exclusion",
            policy_ids=[request.policy_id],
            top_k=2
        )
        room_hits = self.retriever.retrieve(
            query="room rent capping eligibility single private room proportional deduction",
            policy_ids=[request.policy_id],
            top_k=2
        )
        
        all_hits = treatment_hits + room_hits
        citations = CitationLinker.create_citations_from_chunks(all_hits)
        
        # 2. Waiting Period Calculation
        try:
            d_inception = None
            for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                try:
                    d_inception = datetime.strptime(request.policy_inception_date, fmt)
                    break
                except ValueError:
                    pass
            d_incident = None
            for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                try:
                    d_incident = datetime.strptime(request.incident_date, fmt)
                    break
                except ValueError:
                    pass
            if not d_inception or not d_incident:
                raise ValueError("Could not parse dates")
            days_elapsed = (d_incident - d_inception).days
            months_elapsed = max(int(days_elapsed / 30.4), 0)
        except Exception:
            days_elapsed = 365
            months_elapsed = 12
            
        # Determine required waiting period
        required_wp_months = 0
        if treatment_hits:
            ent = treatment_hits[0].get("entities", {})
            required_wp_months = ent.get("waiting_period_months") or (36 if request.is_pre_existing else 0)
            
        is_admissible = True
        status = "Eligible for Claim Processing"
        reason = "Treatment is covered under policy terms and waiting period requirement has been met."
        
        # Check if admission date is before policy inception date
        if days_elapsed < 0:
            is_admissible = False
            status = "Ineligible (Admission Date Precedes Policy Start Date)"
            reason = (
                f"Planned admission date ({request.incident_date}) is earlier than policy start date "
                f"({request.policy_inception_date}). Hospitalization that occurred before the policy began is not covered."
            )
        # Initial 30-day moratorium check
        elif days_elapsed < 30:
            is_admissible = False
            status = "Ineligible (Initial 30-Day Moratorium Active)"
            reason = f"Only {days_elapsed} days have elapsed since policy inception. All non-accidental illnesses are excluded during the initial 30 days."
        elif required_wp_months > 0 and months_elapsed < required_wp_months:
            is_admissible = False
            status = f"Ineligible ({required_wp_months}-Month Waiting Period Active)"
            reason = (
                f"Policy mandates a {required_wp_months}-month waiting period for {request.treatment_name}. "
                f"Only {months_elapsed} months have elapsed since inception date."
            )
            
        # 3. Room Rent Proportional Deduction Math
        allowed_room_rent = request.actual_room_rent_per_day
        room_rent_clause = "Single Private Room / No Capping"
        has_cap = False
        
        if room_hits:
            ent_room = room_hits[0].get("entities", {})
            cap_val = ent_room.get("room_rent_cap")
            if cap_val and "1%" in cap_val:
                has_cap = True
                allowed_room_rent = 5000.0  # Normalized 1% on 5 Lakh Sum Insured base
                room_rent_clause = "Capped at 1% of Sum Insured (₹5,000/day)"
            elif cap_val and "Single Private Room" in cap_val:
                room_rent_clause = "Single Private Room Allowed (No deduction if single room chosen)"
                
        # If user picked deluxe room costing more than allowed
        proportional_factor = 1.0
        disallowed_room_rent = 0.0
        disallowed_associated = 0.0
        
        if has_cap and request.actual_room_rent_per_day > allowed_room_rent:
            proportional_factor = allowed_room_rent / request.actual_room_rent_per_day
            disallowed_room_rent = request.total_room_rent_bill - (request.total_room_rent_bill * proportional_factor)
            disallowed_associated = request.associated_medical_bills * (1.0 - proportional_factor)
            
        total_bill = request.total_room_rent_bill + request.associated_medical_bills
        total_disallowed = disallowed_room_rent + disallowed_associated
        
        # Apply Co-pay (e.g. 10% or 0%)
        copay_percent = 0.0
        if treatment_hits:
            copay_percent = treatment_hits[0].get("entities", {}).get("copay_percent") or 0.0
            
        admissible_before_copay = max(total_bill - total_disallowed, 0.0)
        copay_deduction = admissible_before_copay * (copay_percent / 100.0)
        estimated_settlement = max(admissible_before_copay - copay_deduction, 0.0)
        
        # 4. Document Checklist
        checklist = self._build_checklist(request.hospital_type)
        
        return ClaimsAssessmentResult(
            policy_id=request.policy_id,
            treatment_name=request.treatment_name,
            admissibility_status=status if is_admissible else "Ineligible",
            status_reason=reason,
            waiting_period_details={
                "months_elapsed": months_elapsed,
                "required_waiting_period_months": required_wp_months,
                "is_satisfied": is_admissible
            },
            room_rent_math={
                "room_rent_clause": room_rent_clause,
                "allowed_rate_per_day": allowed_room_rent,
                "actual_rate_per_day": request.actual_room_rent_per_day,
                "proportional_factor": round(proportional_factor, 2),
                "room_rent_penalty": round(disallowed_room_rent, 2),
                "associated_charges_penalty": round(disallowed_associated, 2)
            },
            financial_breakdown={
                "total_hospital_bill": round(total_bill, 2),
                "proportional_deduction_penalty": round(total_disallowed, 2),
                "copay_deduction": round(copay_deduction, 2),
                "estimated_settlement": round(estimated_settlement, 2) if is_admissible else 0.0,
                "estimated_out_of_pocket": round(total_bill - estimated_settlement, 2) if is_admissible else total_bill
            },
            document_checklist=checklist,
            citations=citations
        )

    def _build_checklist(self, hospital_type: str) -> List[str]:
        if hospital_type == "network_cashless":
            return [
                "Filled & Signed Pre-Authorization Request Form (Part A & Part B)",
                "Health Insurance TPA Card & Policy Copy",
                "Government Photo ID Proof of Patient (Aadhaar / Voter ID / Passport)",
                "Consultation Papers & Doctor's Advice for Admission",
                "Diagnostic Test Reports establishing necessity of hospitalization"
            ]
        else:
            return [
                "Duly filled and signed Insurance Reimbursement Claim Form",
                "Original Detailed Discharge Summary (with clinical summary and vitals)",
                "Original Final Hospital Bill with detailed breakup of all charges",
                "Original Payment Receipts with Serial Numbers",
                "Original Pharmacy Bills with Doctor's Prescriptions",
                "Complete Indoor Case Papers (ICP) with Nursing Notes and OT Notes",
                "Diagnostic Reports with Films / Digital Scans (X-Ray, MRI, CT, Blood)",
                "Cancelled Cheque with Proposer's Name printed for NEFT Settlement"
            ]
