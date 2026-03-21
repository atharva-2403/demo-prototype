from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import io

from parser.state_machine import parse_edi

router = APIRouter()

class ReconciliationReport(BaseModel):
    total_claims: int
    matched_claims: int
    unmatched_claims: int
    discrepancies: List[Dict[str, Any]]
    details: List[Dict[str, Any]]

@router.post("/reconcile", response_model=ReconciliationReport)
async def reconcile_claims(
    file_837: UploadFile = File(...), 
    file_835: UploadFile = File(...)
):
    try:
        content_837 = await file_837.read()
        text_837 = content_837.decode("utf-8", errors="replace")
        parsed_837 = parse_edi(text_837)
        
        content_835 = await file_835.read()
        text_835 = content_835.decode("utf-8", errors="replace")
        parsed_835 = parse_edi(text_835)

        if parsed_837.transaction_type not in ["837P", "837I"]:
            raise HTTPException(status_code=400, detail="The first file must be an 837 claim (837P or 837I).")
        if parsed_835.transaction_type != "835":
            raise HTTPException(status_code=400, detail="The second file must be an 835 remittance advice.")

        # Extract claims from 837
        claims = {}
        def extract_claims_837(loops):
            for loop in loops:
                if loop.loop_id == "2300":
                    clm_seg = next((s for s in loop.segments if s.id == "CLM"), None)
                    if clm_seg:
                        # CLM01 is claim submitter id
                        claim_id = next((e.value for e in clm_seg.elements if e.position == 1), None)
                        # CLM02 is total charge amount
                        billed_amt = next((e.value for e in clm_seg.elements if e.position == 2), "0")
                        if claim_id:
                            claims[claim_id] = {"billed": float(billed_amt), "paid": 0.0, "adjustments": []}
                extract_claims_837(loop.children)
                
        extract_claims_837(parsed_837.loops)
        
        # Extract payments from 835
        payments = {}
        def extract_payments_835(loops):
            for loop in loops:
                if loop.loop_id == "2100":
                    clp_seg = next((s for s in loop.segments if s.id == "CLP"), None)
                    if clp_seg:
                        # CLP01 is claim submitter id
                        claim_id = next((e.value for e in clp_seg.elements if e.position == 1), None)
                        # CLP03 is total claim charge amount
                        # CLP04 is claim payment amount
                        paid_amt = next((e.value for e in clp_seg.elements if e.position == 4), "0")
                        
                        adjustments = []
                        # CAS segments usually belong directly to the 2100 loop or 2110
                        for seg in loop.segments:
                            if seg.id == "CAS":
                                group_code = next((e.value for e in seg.elements if e.position == 1), "")
                                reason_code = next((e.value for e in seg.elements if e.position == 2), "")
                                adj_amount = next((e.value for e in seg.elements if e.position == 3), "0")
                                adjustments.append({
                                    "group_code": group_code,
                                    "reason_code": reason_code,
                                    "amount": float(adj_amount)
                                })
                        
                        for child in loop.children:
                            if child.loop_id == "2110":
                                for seg in child.segments:
                                    if seg.id == "CAS":
                                        group_code = next((e.value for e in seg.elements if e.position == 1), "")
                                        reason_code = next((e.value for e in seg.elements if e.position == 2), "")
                                        adj_amount = next((e.value for e in seg.elements if e.position == 3), "0")
                                        adjustments.append({
                                            "group_code": group_code,
                                            "reason_code": reason_code,
                                            "amount": float(adj_amount)
                                        })
                        
                        if claim_id:
                            payments[claim_id] = {
                                "paid": float(paid_amt),
                                "adjustments": adjustments
                            }
                extract_payments_835(loop.children)
                
        extract_payments_835(parsed_835.loops)

        # Cross-reference and reconcile
        total_claims = len(claims)
        matched_claims = 0
        unmatched_claims = 0
        discrepancies = []
        details = []

        for claim_id, claim_data in claims.items():
            if claim_id in payments:
                matched_claims += 1
                payment_data = payments[claim_id]
                
                billed = claim_data["billed"]
                paid = payment_data["paid"]
                adjs = payment_data["adjustments"]
                
                total_adj = sum(a["amount"] for a in adjs)
                
                # Math check: Billed - Paid - Adjustments should ideally be near zero
                diff = abs(billed - paid - total_adj)
                has_discrepancy = diff > 0.01
                
                rec_detail = {
                    "claim_id": claim_id,
                    "billed_amount": billed,
                    "paid_amount": paid,
                    "adjustments": adjs,
                    "reconciliation_difference": round(diff, 2),
                    "is_balanced": not has_discrepancy
                }
                
                details.append(rec_detail)
                if has_discrepancy:
                    discrepancies.append(rec_detail)
            else:
                unmatched_claims += 1

        return ReconciliationReport(
            total_claims=total_claims,
            matched_claims=matched_claims,
            unmatched_claims=unmatched_claims,
            discrepancies=discrepancies,
            details=details
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reconciling files: {str(e)}")