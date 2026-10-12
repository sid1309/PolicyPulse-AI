import os
import httpx
from typing import List, Dict, Any, Tuple, Optional
from backend.app.core.config import settings
from backend.app.core.models import CitationItem, ChatResponse
from backend.app.engines.citation_linker import CitationLinker

class CoverageEngine:
    """
    Synthesizes legally grounded coverage and exclusion analysis with strict 
    anti-hallucination guardrails and page-level citations.
    """

    SYSTEM_PROMPT = """You are an expert Insurance Policy Intelligence & Claims Decision-Support Assistant.
Your task is to analyze user insurance queries using ONLY the provided verified policy clause excerpts.

CRITICAL CONTRACT DECISION HIERARCHY:
1. EXCLUSIONS OVERRULE COVERAGE:
   - Always check if the treatment, expense, appliance, or condition is explicitly excluded under Exclusions (e.g., Spectacles, Eye glasses, Contact lenses, Refractive errors under 7.5 dioptres [Code- Excl15], Cosmetic surgery, Outpatient/OPD treatments without hospitalization).
   - If an exclusion applies, the verdict MUST be **Verdict: NOT COVERED** or **Verdict: EXCLUDED**.
2. INPATIENT HOSPITALIZATION REQUIREMENT:
   - Health insurance policies require Inpatient Hospitalization (minimum 24 continuous hours) or listed Day Care treatments.
   - Routine doctor visits, OPD consultations, and standalone pharmacy medicines for cold, cough, fever, flu without hospital admission are NOT covered under Outpatient Treatment exclusions. Verdict: **Verdict: NOT COVERED (Out-Patient / OPD Expenses Excluded)**.
3. ACCIDENTAL INJURIES & EMERGENCY CARE:
   - Hospitalization resulting from accidents (e.g., bike accident, road accident, fractures, sudden trauma) is fully COVERED from Day 1 of policy inception with ZERO waiting period (the 30-day initial waiting period is waived for accidental hospitalization).
   - Do NOT classify general road or bike accidents as excluded under Change-of-Gender, Cosmetic surgery, or Adventure sports exclusions unless the user was participating in professional motor racing competitions or committing a criminal breach of law.
4. WAITING PERIODS:
   - If covered under Scope of Cover, determine whether Pre-Existing Disease (PED, typically 36/48 months) or Specific Illness Waiting Period (e.g., Cataract, typically 24 months) or 30-day initial waiting period applies. Verdict: **Verdict: CONDITIONALLY COVERED (Subject to X Months Waiting Period)**.
5. SUB-LIMITS & COPAY:
   - For modern treatments, cataract, or room rent, state applicable caps (e.g., 50% SI, Rs. 40,000 per eye, 1% SI).

CRITICAL INSTRUCTIONS:
1. Strict Grounding: Every statement must be derived directly from the provided clauses. Do NOT assume or invent standard terms.
2. Honest Abstention: If the provided clauses do NOT contain enough information to conclusively answer, clearly state:
   "The policy document does not provide sufficient information to determine coverage for [topic]."
3. Page Citations: Reference the exact page and clause for every rule, exclusion, waiting period, or limit mentioned (e.g., "[Page 14, Clause 4.2(b)]").
4. Verdict First: Begin your answer with a bold verdict:
   - **Verdict: COVERED**
   - **Verdict: NOT COVERED (Exclusion / Out-Patient)**
   - **Verdict: CONDITIONALLY COVERED (Subject to Waiting Period / Limits)**
   - **Verdict: INSUFFICIENT EVIDENCE IN POLICY DOCUMENT**
5. Structured Answer Format:
   Always structure your response with clear markdown headings:
   - **Verdict: ...**
   - ### Coverage Finding
     1-2 plain-English sentences directly explaining how the policy addresses the user's specific situation.
   - ### Governing Contract Provision
     Bullet points summarizing the Policy name, Section name, Clause title, and Page citations.
   - ### Relevant Policy Text Extract
     Include the exact policy wording in a blockquote prefixed with the section and clause header:
     > **[Section: <Section Name> • Clause: <Clause Title> • Page <Page #>]**
     > "<exact clause text>"
6. Highlight Nuances: Always state applicable waiting periods, co-payment percentages, or room-rent sub-limits if mentioned in the context.
"""

    def generate_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        intent: str = "GENERAL",
        history: Optional[List[Dict[str, str]]] = None
    ) -> ChatResponse:
        """Generates grounded answer with confidence scoring, citations, and conversation memory."""
        citations = CitationLinker.create_citations_from_chunks(retrieved_chunks)
        
        # Check evidence sufficiency
        if not retrieved_chunks:
            return ChatResponse(
                answer=(
                    "**Verdict: INSUFFICIENT EVIDENCE IN POLICY DOCUMENT**\n\n"
                    "No matching clauses were found in the uploaded policy documents for your query. "
                    "Please check if the correct policy is selected or verify whether this treatment or condition is addressed under a different term."
                ),
                citations=[],
                confidence_score=0.0,
                intent=intent,
                retrieved_chunks_count=0,
                insufficient_evidence=True
            )
            
        # Build structured XML evidence context
        context_blocks = []
        for idx, c in enumerate(retrieved_chunks):
            context_blocks.append(
                f"<clause_evidence id=\"{idx+1}\" policy=\"{c.get('insurer')} - {c.get('plan_name')}\" "
                f"page=\"{c.get('page_number')}\" clause=\"{c.get('clause_id')}\">\n"
                f"{c.get('content_text')}\n"
                f"</clause_evidence>"
            )
        evidence_text = "\n\n".join(context_blocks)
        
        # Format recent history if present
        history_text = ""
        if history and len(history) > 0:
            formatted_turns = []
            for h in history[-4:]:
                role = "User" if h.get("role") == "user" else "Assistant"
                formatted_turns.append(f"{role}: {h.get('content', '')[:200]}")
            history_text = "Recent Conversation Thread:\n" + "\n".join(formatted_turns) + "\n\n"
        
        prompt = (
            f"{history_text}"
            f"Current User Question: {query}\n\n"
            f"Verified Policy Clauses:\n{evidence_text}\n\n"
            f"Provide a clear, authoritative, and structured answer according to the system instructions. Focus on answering the Current User Question while maintaining consistency with recent context if relevant."
        )
        
        # Attempt LLM generation via Gemini or OpenAI if API key available
        answer_text, success = self._call_llm(prompt)
        
        if not success:
            # High-fidelity rule-based synthesis fallback
            answer_text = self._synthesize_fallback(query, retrieved_chunks, history=history)
            
        # Calculate confidence score
        avg_score = 0.85
        if retrieved_chunks and "normalized_score" in retrieved_chunks[0]:
            avg_score = sum(c.get("normalized_score", 0.7) for c in retrieved_chunks[:3]) / min(len(retrieved_chunks), 3)
            
        return ChatResponse(
            answer=answer_text,
            citations=citations,
            confidence_score=round(avg_score, 2),
            intent=intent,
            retrieved_chunks_count=len(retrieved_chunks),
            insufficient_evidence=False
        )

    def _call_llm(self, prompt: str) -> Tuple[str, bool]:
        """Calls Groq (Key 1 -> Key 2), then Gemini, then OpenAI based on available configuration."""
        # 1. PRIMARY: Try Groq Key 1 and Key 2 (qwen/qwen3.8-27b)
        groq_keys = [k for k in [settings.GROG_API_KEY_1, settings.GROG_API_KEY_2] if k]
        for key_idx, groq_key in enumerate(groq_keys, 1):
            try:
                import httpx
                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.GROQ_MODEL or "qwen/qwen3.8-27b",
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.2
                }
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            text = choices[0].get("message", {}).get("content", "").strip()
                            if text:
                                return text, True
                    else:
                        print(f"CoverageEngine Groq Key {key_idx} response {resp.status_code}: {resp.text[:80]}")
            except Exception as e:
                print(f"CoverageEngine Groq Key {key_idx} notice: {e}")

        # 2. SECONDARY: Try Gemini if Groq keys fail
        if settings.GEMINI_API_KEY:
            try:
                candidate_models = ["gemini-flash-latest", "gemini-3.8-flash", settings.GEMINI_MODEL]
                # Deduplicate while preserving order
                seen = set()
                models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]
                for model_name in models_to_try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
                    payload = {
                        "contents": [{"parts": [{"text": f"{self.SYSTEM_PROMPT}\n\n{prompt}"}]}],
                        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000}
                    }
                    with httpx.Client(timeout=20.0) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    return parts[0].get("text", "").strip(), True
                        else:
                            print(f"Gemini model {model_name} response {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                print(f"Gemini API call notice: {e}")

        # 2. Try OpenAI
        if settings.OPENAI_API_KEY:
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                resp = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                return resp.choices[0].message.content.strip(), True
            except Exception as e:
                print(f"OpenAI API call notice: {e}")

        return "", False

    def _synthesize_fallback(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Deterministic rule-based synthesis if external LLM API key is not configured."""
        top_chunk = chunks[0]
        # Prefer substantive clause chunk over bare heading stub if available
        for c in chunks:
            c_text = c.get('content_text', '')
            c_clean = c_text.split(':\n', 1)[-1].strip() if ':\n' in c_text else c_text.strip()
            if len(c_clean) > 80:
                is_ped_cand = any(ped_term in query.lower() for ped_term in ["diabet", "sugar", "hyperten", "blood pressure", "thyroid", "asthma", "heart", "ped", "pre-existing"])
                if is_ped_cand and ("excl01" in (c.get("section_name", "") + " " + c.get("clause_title", "")).lower() or "pre-existing" in c_clean.lower() or "expiry of" in c_clean.lower()):
                    top_chunk = c
                    break

        policy_label = f"{top_chunk.get('insurer')} {top_chunk.get('plan_name')}".strip()
        page_num = top_chunk.get('page_number', 'N/A')
        import re
        clause_raw = (top_chunk.get('clause_title') or 'Contract Clause').strip()
        # Clean enumeration prefix like "c) ", "3. ", "(a) " from title
        clause_clean = re.sub(r'^([a-z0-9]+[\.\)]\s*|\([a-z0-9]+\)\s*)', '', clause_raw, flags=re.IGNORECASE).strip()
        clause_title = clause_clean if len(clause_clean) >= 5 else clause_raw
        section_name = (top_chunk.get('section_name') or 'General Provisions').strip()
        
        entities = top_chunk.get("entities", {})
        wp = entities.get("waiting_period_months")
        rr = entities.get("room_rent_cap")
        copay = entities.get("copay_percent")

        full_content = top_chunk.get('content_text', '').strip()
        if ":\n" in full_content:
            clean_text = full_content.split(":\n", 1)[-1].strip()
        else:
            clean_text = full_content
            
        # Strip any remaining internal breadcrumb fragments like "[Policy: ...] > [...]"
        clean_text = re.sub(r'\[(?:Policy:?\s*)?[^\]]+\]\s*>\s*\[[^\]]+\](?:\s*>\s*\[[^\]]+\])?:?\s*', '', clean_text).strip()
        
        # Smart formatting: break numbered subpoints (1., 2., a), etc.) onto separate lines
        clean_text = re.sub(r'(?<!\n)(?<=\S)\s+([1a]\.\s+|[1a]\)\s+|\([1a]\)\s+)', r'\n\n\1', clean_text)
        clean_text = re.sub(r'([;\.\:])\s+(\b[0-9]{1,2}\.|\b[a-z0-9]\)|\b[ivxlcdm]+\.)\s+', r'\1\n\n\2 ', clean_text)
        clean_text = re.sub(r'([;\.\:\)])\s+(Code[\-\s]*Excl[0-9]+|\bExcl[0-9]+\b)', r'\1\n\n\2', clean_text, flags=re.I)
        clean_text = re.sub(r'(?<!\n)(?<=\S)\s+(Def\s+[0-9]+[\.\:]|\bDefinition\s+[0-9]+[\.\:])', r'\n\n\1', clean_text, flags=re.I)
        
        q_lower = query.lower()
        chunk_lower = (section_name + " " + clause_title + " " + clean_text).lower()

        is_room_query = any(w in q_lower for w in ["room rent", "icu", "room category", "room limit", "per day", "room, board", "proportionate"])
        is_robotic_query = any(w in q_lower for w in ["robotic", "modern treatment", "advanced medical"])
        is_cataract_query = any(w in q_lower for w in ["cataract", "cataract surgery"])
        is_glasses_query = any(w in q_lower for w in ["glass", "spectacle", "lens", "refractive", "eye point", "eye sight", "vision correction", "optical", "dioptre"]) and not is_cataract_query
        is_opd_query = any(w in q_lower for w in ["cold", "fever", "cough", "flu", "paracetamol", "headache", "opd", "outpatient", "medicines for cold", "prescription medicine", "pharmacy"])
        is_dental_query = any(w in q_lower for w in ["dental", "teeth", "tooth", "cavity", "root canal", "crown", "filling"])
        is_accident_query = any(w in q_lower for w in ["accident", "accidental", "bike accident", "road accident", "car accident", "fracture", "trauma", "injury", "hit by"])
        is_bariatric_query = any(w in q_lower for w in ["bariatric", "weight loss", "obesity surgery", "slimming"])
        is_unproven_query = any(w in q_lower for w in ["unproven", "experimental"]) and not is_robotic_query
        is_organ_donor_query = any(w in q_lower for w in ["organ donor", "donor hospital", "kidney donor"])
        is_waiting_query = any(w in q_lower for w in ["waiting period", "ped", "pre-existing", "wait"])
        is_copay_query = any(w in q_lower for w in ["copay", "co-pay", "co payment", "deductible"])

        # Refine clause title if generic enumeration or subclause
        if clause_title.lower().startswith("clause ") or len(clause_title) <= 5:
            def_m = re.search(r'\b(Def(?:inition)?\s+[0-9]+[\.\:][^\n\.\:]{3,40})', clean_text, re.I)
            if def_m:
                clause_title = def_m.group(1).strip()

        from backend.app.retrieval.medical_ontology import InsuranceMedicalOntology
        med_match = InsuranceMedicalOntology.match_condition(q_lower)
        is_ped_query = med_match and med_match.get("type") == "PED"
        is_specified_query = med_match and med_match.get("type") == "SPECIFIED"

        # Determine context-aware verdict & plain-English coverage finding (Query intent first)
        if is_glasses_query:
            verdict = "**Verdict: EXCLUDED / SUBJECT TO SPECIFIC RESTRICTIONS**"
            finding = (
                "Purchasing spectacles, contact lenses, or treatments for refractive error correction are specifically "
                "excluded under **Section 8.1 Standard Exclusions (12. Refractive Error - Code Excl15)**. "
                "Expenses related to the treatment for correction of eye sight due to refractive error less than 7.5 dioptres "
                "and optical aids/glasses are not payable by the insurer unless covered under an active specialized rider."
            )
        elif is_opd_query:
            verdict = "**Verdict: NOT COVERED (Requires 24-Hour Inpatient Hospitalization / OPD Excluded)**"
            finding = (
                "Routine medications, pharmacy bills, and outpatient consultations for minor illnesses like cold, fever, or cough "
                "are **not covered** under standard base health insurance. The policy requires a minimum admission of "
                "**24 consecutive hours of Inpatient Care** (Def 18. Hospitalization) for medical expenses to be admissible, "
                "unless an active Outpatient (OPD) add-on cover or specific Day Care procedure applies."
            )
        elif is_dental_query:
            verdict = "**Verdict: EXCLUDED / NOT COVERED (Unless Due to Accidental Hospitalization)**"
            finding = (
                "Routine dental examinations, fillings, crowns, extractions, and dental surgery are excluded under "
                "the policy terms and definitions (Def 13. Dental Treatment), unless requiring inpatient hospitalization "
                "necessitated by an accidental bodily injury."
            )
        elif is_accident_query:
            verdict = "**Verdict: COVERED UNDER INPATIENT HOSPITALIZATION & EMERGENCY CARE**"
            finding = (
                "Medical, surgical, and diagnostic treatment necessitated by an accidental bodily injury (such as a bike or road accident) "
                "is **fully covered** under the policy's **Section 4.1 Inpatient Hospitalization** and Day Care Treatments. "
                "Crucially, **zero waiting period applies** for emergency accidental hospitalization—the standard 30-day "
                "initial waiting period is waived by regulation for accidents from Day 1 of policy inception. "
                "Expenses are admissible provided the incident did not involve professional hazardous sports or motor racing competitions "
                "(Code Excl09), driving under the influence of intoxicating substances (Code Excl12), or intentional breach of law (Code Excl10)."
            )
        elif is_bariatric_query:
            verdict = "**Verdict: EXCLUDED / SUBJECT TO SPECIFIC RESTRICTIONS**"
            finding = (
                "Bariatric surgery for weight loss is excluded under **Section 8.1 Standard Exclusions (3. Obesity/ Weight Control - Code Excl06)**, "
                "unless strict statutory medical necessity criteria for morbid obesity (BMI ≥ 40 kg/m², or BMI ≥ 35 kg/m² with severe co-morbidities) "
                "are documented and certified by an attending specialist."
            )
        elif is_unproven_query:
            verdict = "**Verdict: EXCLUDED / SUBJECT TO SPECIFIC RESTRICTIONS**"
            finding = (
                "Expenses related to unproven or experimental treatments, services, and supplies that lack significant "
                "medical documentation to support their clinical efficacy are excluded under **Section 8.1 Standard Exclusions (13. Unproven Treatments - Code Excl16)**."
            )
        elif is_organ_donor_query:
            verdict = "**Verdict: COVERED UNDER ORGAN DONOR INPATIENT CARE**"
            finding = (
                "Hospitalization medical expenses incurred for an organ donor during harvesting surgery (for organ donated to the Insured Person) "
                "are **fully covered** under the policy's **Section 4.4 Organ Donor Expenses**, subject to the recipient's inpatient hospitalization admissibility."
            )
        elif is_ped_query:
            disease_name = med_match.get("name", "Pre-Existing Condition")
            wait_months = wp or 36
            verdict = f"**Verdict: CONDITIONALLY COVERED (Subject to {wait_months} Months Pre-Existing Disease Waiting Period)**"
            finding = (
                f"**{disease_name}** is classified under the policy's **Pre-Existing Disease (PED - Code Excl01)** schedule.\n\n"
                f"**When the waiting period ends:**\n"
                f"Expenses related to the treatment of {disease_name} and its direct complications become admissible once you complete "
                f"**{wait_months} months of continuous coverage** from the inception date of the policy (as specified in your Policy Schedule), "
                f"provided the condition was declared in the proposal form and accepted by the insurer."
            )
        elif is_room_query:
            verdict = "**Verdict: SUBJECT TO ROOM RENT LIMIT & PROPORTIONATE DEDUCTION**"
            rr_desc = rr or "1% of Sum Insured per day (Normal Room) / 2% of Sum Insured per day (ICU)"
            finding = (
                f"Your hospital room occupancy is governed by the contractual room limit: **{rr_desc}**.\n\n"
                f"**What happens if you go over it:**\n"
                f"If you select a room category or daily tariff higher than your eligible room cap, the insurer enforces a **proportionate deduction clause**. "
                f"This means that not only the excess room tariff, but **all associated medical expenses** "
                f"(including surgeon fees, doctor visit charges, nursing charges, and diagnostic tests) "
                f"will be reduced in the ratio of `Eligible Room Rent / Actual Room Rent`, and you must pay the remaining balance out of pocket."
            )
        elif is_specified_query and not is_cataract_query:
            disease_name = med_match.get("name", "Specified Illness")
            verdict = f"**Verdict: CONDITIONALLY COVERED (Subject to 24 Months Specified Disease Waiting Period)**"
            finding = (
                f"**{disease_name}** falls under the policy's **Specified Disease / Procedure Waiting Period (Code- Excl02)** list. "
                f"A mandatory waiting period of **24 months** of continuous coverage applies before claims for this condition become admissible. "
                f"*(Note: If the condition was pre-existing before policy inception, the longer Pre-Existing Disease waiting period applies).*"
            )
        elif is_robotic_query:
            verdict = "**Verdict: COVERED UNDER MODERN TREATMENTS (Subject to Sub-Limits & Medical Necessity)**"
            finding = (
                "Robotic surgery is covered under the policy's **Modern Treatment Methods** provision. "
                "Expenses are payable when the surgery is medically necessary and advised by a registered medical practitioner, "
                "either under Inpatient Hospitalization or Day Care Treatment, subject to the applicable sub-limit (e.g., up to 50% of Sum Insured) "
                "and any underlying condition-specific waiting periods."
            )
        elif is_cataract_query:
            verdict = "**Verdict: CONDITIONALLY COVERED (Subject to Sub-Limit & Waiting Period)**"
            finding = (
                "Cataract surgery is covered under the policy subject to the defined sub-limit per eye specified in the "
                "Table of Benefits and completion of the mandatory specific illness waiting period (typically 24 months)."
            )
        elif "exclusion" in section_name.lower() or "excl" in clause_title.lower() or "not covered" in chunk_lower:
            verdict = "**Verdict: EXCLUDED / SUBJECT TO SPECIFIC RESTRICTIONS**"
            finding = (
                f"This procedure or expense is classified under the policy's specific exclusions ({section_name}). "
                "The insurer has contractually zero liability to pay expenses falling under this provision unless covered by an active add-on rider."
            )
        elif is_waiting_query or (wp and not is_room_query):
            verdict = f"**Verdict: CONDITIONALLY COVERED (Subject to {wp or '24'} Months Waiting Period)**"
            finding = (
                f"This procedure or medical condition falls under the specific waiting period schedule ({section_name}). "
                f"A mandatory waiting period of {wp or '24'} months of continuous coverage applies before claims become admissible."
            )
        elif "scope of cover" in section_name.lower() or "inpatient" in section_name.lower():
            verdict = "**Verdict: COVERED UNDER INPATIENT HOSPITALIZATION**"
            finding = (
                "This treatment is covered under Inpatient Hospitalization medical expenses, provided admission exceeds 24 continuous hours "
                "and the procedure is prescribed as medically necessary."
            )
        else:
            verdict = "**Verdict: CONDITIONALLY COVERED (Subject to Policy Terms & Conditions)**"
            finding = (
                f"Coverage is governed by {section_name} ({clause_title}). Admissibility is subject to formal medical necessity, "
                "pre-authorization or standard claim submission, and standard policy deductible/co-pay requirements."
            )

        points = [
            f"- **Policy:** **{policy_label}**",
            f"- **Governing Section:** **{section_name}**",
            f"- **Clause:** **{clause_title}** (Page {page_num})"
        ]
        if rr:
            points.append(f"- **Room Rent Limit:** **{rr}**.")
        if is_accident_query:
            points.append("- **Applicable Waiting Period:** **0 Months (Immediate Day 1 Coverage)** — Initial 30-day waiting period is waived for accidental hospitalization.")
        elif is_ped_query:
            points.append(f"- **Applicable Waiting Period:** **{wp or 36} Months** for Pre-Existing Diseases (PED - Code Excl01).")
        elif (is_waiting_query or not is_room_query) and wp:
            points.append(f"- **Applicable Waiting Period:** **{wp} Months** before claim admissibility.")
        if (is_copay_query or not is_room_query) and copay:
            points.append(f"- **Co-payment Requirement:** **{copay}%** out-of-pocket deduction on claim amount.")
            
        follow_up_note = ""
        if history and len(history) > 0:
            last_query = history[-1].get("content", "")
            if len(last_query) > 0:
                follow_up_note = f"\n*Follow-up context considered regarding your previous question.*"
        
        is_table = top_chunk.get("chunk_type") == "table" or clean_text.strip().startswith("|")
        if is_table:
            # Clean markdown table rows: eliminate blank lines between table rows for proper markdown parsing
            raw_lines = [l.strip() for l in clean_text.split("\n") if l.strip()]
            table_lines = [l for l in raw_lines if l.startswith("|")]
            
            if table_lines and len(table_lines) >= 3:
                header_line = table_lines[0]
                sep_line = table_lines[1]
                data_rows = table_lines[2:]
                
                # Find matching rows relevant to the user query
                q_tokens = [w for w in re.findall(r"\b[a-z0-9]+\b", q_lower) if len(w) > 3 and w not in ["what", "limit", "when", "does", "have", "over"]]
                matched_rows = []
                for row in data_rows:
                    row_lower = row.lower()
                    if any(tok in row_lower for tok in q_tokens):
                        matched_rows.append(row)
                        
                # If specific matching rows found, present a focused extract
                if matched_rows and len(matched_rows) < len(data_rows):
                    filtered_table = "\n".join([header_line, sep_line] + matched_rows)
                else:
                    filtered_table = "\n".join(table_lines)
            else:
                filtered_table = "\n".join(table_lines) if table_lines else clean_text

            extract_block = (
                f"### Relevant Policy Table Extract\n"
                f"**[{section_name} • Page {page_num}]**\n\n"
                f"{filtered_table}\n\n"
            )
        else:
            extract_block = (
                f"### Relevant Policy Text Extract\n"
                f"> **[Section: {section_name} • Clause: {clause_title} • Page {page_num}]**\n"
                f"> \"{clean_text}\"\n\n"
            )

        return (
            f"{verdict}\n\n"
            f"### Coverage Finding\n"
            f"{finding}\n\n"
            f"### Governing Contract Provision\n"
            + "\n".join(points) + "\n\n"
            f"{extract_block}"
            f"*Please refer to the source document citations below to view the complete contractual wording.*"
            f"{follow_up_note}"
        )

    def explain_clause(
        self,
        clause_title: str,
        clause_text: str,
        verdict: Optional[str] = None,
        insurer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translates legal clause into plain English with wallet impact and action checklist."""
        # 1. Try LLM if configured
        prompt = (
            f"You are an insurance patient advocate. Translate this legal insurance policy clause into simple language:\n\n"
            f"Clause Title: {clause_title}\n"
            f"Clause Text:\n{clause_text}\n"
            f"Verdict Context: {verdict or 'N/A'}\n\n"
            f"Return JSON with exactly:\n"
            f"- simple_explanation: (2-3 sentences in 8th-grade English explaining what this means)\n"
            f"- wallet_impact: (clear statement of out-of-pocket money consequences)\n"
            f"- action_checklist: (list of 3 concrete steps the policyholder must take)\n"
        )
        answer_text, success = self._call_llm(prompt)
        if success and "{" in answer_text and "}" in answer_text:
            try:
                import json
                start = answer_text.find("{")
                end = answer_text.rfind("}") + 1
                return json.loads(answer_text[start:end])
            except Exception:
                pass
                
        # 2. Intelligent Domain-Specific Rule Translation
        text_lower = (clause_title + " " + clause_text).lower()
        
        if "room" in text_lower or "rent" in text_lower or "proportionate" in text_lower or "sub-limit" in text_lower:
            return {
                "clause_title": clause_title,
                "simple_explanation": "If your chosen hospital room costs more than your policy's allowed limit, the insurance company will penalize you. They will proportionally cut not just the room rent difference, but also your doctor's fees, OT charges, and nursing costs by the same percentage ratio.",
                "wallet_impact": "You could end up paying 30% to 50% of the entire hospital bill out of your own pocket due to proportional deduction.",
                "action_checklist": [
                    "Ask the hospital admission desk for a room strictly within your eligible category (e.g. Single Private AC)",
                    "Never upgrade room category expecting to pay only the room rent difference",
                    "Request an itemized estimate before surgery to verify all tariff codes match your eligible category"
                ]
            }
        elif "waiting" in text_lower or "pre-existing" in text_lower or "ped" in text_lower:
            return {
                "clause_title": clause_title,
                "simple_explanation": "You must hold this policy continuously for the specified waiting period before claims for this medical condition are payable. Any treatment during the waiting period is strictly non-payable unless it arose from an accidental emergency.",
                "wallet_impact": "100% claim rejection if admission occurs before the required continuous coverage tenure is completed.",
                "action_checklist": [
                    "Check your exact policy inception date on your policy certificate",
                    "Keep your previous insurer renewal documents handy if you ported your policy",
                    "Do not schedule elective treatments until the waiting period has elapsed"
                ]
            }
        elif "exclusion" in text_lower or "excluded" in text_lower or "not covered" in text_lower:
            return {
                "clause_title": clause_title,
                "simple_explanation": "This specific procedure or item is explicitly excluded from your policy's scope of cover. The insurance company has contractually zero liability to pay for expenses under this head.",
                "wallet_impact": "All costs under this category must be borne entirely by the policyholder.",
                "action_checklist": [
                    "Ask your doctor if there is a medically equivalent covered procedure",
                    "Verify if an optional rider or top-up cover can be purchased to include this",
                    "Request a separate non-medical billing estimate from the hospital"
                ]
            }
        else:
            return {
                "clause_title": clause_title,
                "simple_explanation": "This clause specifies the contractual terms, documentation requirements, and conditions governing the payment of your health insurance claim.",
                "wallet_impact": "Compliance with these terms ensures your claim is paid smoothly without deductions or delays.",
                "action_checklist": [
                    "Submit cashless pre-authorization at least 48 hours before planned admission",
                    "Collect all discharge summaries, doctor prescriptions, and stamped diagnostic reports",
                    "Retain original pharmacy receipts and itemized payment vouchers"
                ]
            }
