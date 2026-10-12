import re
from typing import Dict, Any, List

class QueryRouter:
    """
    Analyzes intent, expands medical/insurance terminology, 
    and determines the optimal retrieval strategy.
    """

    EXPANSION_RULES = {
        "cataract": "cataract eye surgery ophthalmology 24 months waiting period",
        "hernia": "hernia hydrocele medical or surgical treatment 24 months waiting period",
        "kidney stone": "renal calculi urinary stones lithotripsy 24 months waiting period",
        "gall bladder": "gall bladder stones cholecystectomy 24 months waiting period",
        "joint replacement": "joint replacement knee hip osteoarthritis 48 months waiting period",
        "high blood pressure": "hypertension pre-existing disease cardiac condition",
        "bp": "hypertension pre-existing disease",
        "diabetes": "diabetes mellitus endocrine disorder pre-existing disease",
        "sugar": "diabetes mellitus pre-existing disease",
        "robotic surgery": "robotic surgeries modern treatment methods advanced surgical technology sub-limit daycare inpatient",
        "robotic": "robotic surgeries modern treatments advanced medical procedures sub-limit daycare",
        "room rent": "room rent capping single private room charges proportional deduction",
        "icu": "intensive care unit charges sub-limit",
        "co-pay": "co-payment mandatory co-pay zone copay deductible",
        "copay": "co-payment mandatory co-pay percentage deductible",
        "waiting period": "waiting period 30 days initial waiting specific disease 24 months pre-existing 36 48 months",
        "ped": "pre-existing diseases declared at inception waiting period",
        "maternity": "maternity expenses child birth normal delivery c-section waiting period",
        "cashless": "cashless facility network provider pre-authorization claim procedure",
        "reimbursement": "reimbursement claim documentation discharge summary bills papers",
        "glasses": "spectacles refractive error contact lenses optical Exclusions permanent",
        "spectacles": "spectacles refractive error contact lenses optical Exclusions permanent",
        "eye point": "refractive error spectacles eye sight correction Exclusions",
        "eye power": "refractive error spectacles eye sight correction Exclusions",
        "vision": "refractive error spectacles eye sight correction Exclusions",
        "cold": "outpatient diagnostic OPD treatments non-prescribed drugs medicines inpatient hospitalization minimum 24 hours",
        "fever": "outpatient diagnostic OPD treatments non-prescribed drugs medicines inpatient hospitalization minimum 24 hours",
        "cough": "outpatient diagnostic OPD treatments non-prescribed drugs medicines inpatient hospitalization minimum 24 hours",
        "flu": "outpatient diagnostic OPD treatments non-prescribed drugs medicines inpatient hospitalization minimum 24 hours",
        "opd": "outpatient diagnostic medical surgical procedures non-prescribed drugs",
        "outpatient": "outpatient diagnostic medical surgical procedures non-prescribed drugs",
        "dental": "dental treatment surgery hospitalization accidental bodily injury",
        "accident": "accidental bodily injury hospitalization emergency care Day Care Treatment Section 4.1 Inpatient Hospitalization",
        "bike accident": "accidental bodily injury hospitalization emergency care Day Care Treatment Section 4.1 Inpatient Hospitalization",
        "injury": "accidental injury bodily harm hospitalization emergency care Day Care Treatment Section 4.1",
        "bariatric": "bariatric surgery obesity weight loss weight control morbid obesity Code- Excl06 permanent exclusion",
        "weight loss": "bariatric surgery obesity weight control Code- Excl06 permanent exclusion",
        "unproven": "unproven treatments experimental stem cell therapy Code- Excl16 permanent exclusion",
        "organ donor": "organ donor Section 4.4 harvesting hospitalization expenses covered for insured recipient"
    }

    @classmethod
    def get_dynamic_llm_expansion(cls, query: str) -> str:
        """Dynamically generates legal and contractual insurance search terms via LLM as primary query rewriter."""
        from backend.app.core.config import settings
        prompt = (
            f"You are an insurance search optimizer. Convert this user question into 4-7 specific contractual, legal, or medical keywords and potential section names (e.g. Exclusions, OPD, Inpatient, Waiting Periods, clause codes) to search within an insurance contract PDF.\n"
            f"Question: \"{query}\"\n"
            f"Output ONLY a space-separated string of search terms, no explanation."
        )

        # 1. PRIMARY: Try Groq Key 1 (qwen/qwen3.8-27b)
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
                        {"role": "system", "content": "You are an insurance search optimizer. Convert the user question into 4-7 specific contractual, legal, or medical keywords and potential section names (e.g. Exclusions, OPD, Inpatient, Waiting Periods, clause codes). Output ONLY a space-separated string of search terms, no explanation, no punctuation."},
                        {"role": "user", "content": query}
                    ],
                    "max_tokens": 40,
                    "temperature": 0.1
                }
                with httpx.Client(timeout=4.0) as client:
                    resp = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            text = choices[0].get("message", {}).get("content", "").strip()
                            if text:
                                return text.replace("\n", " ").replace('"', '')
                    else:
                        print(f"Groq Key {key_idx} response {resp.status_code}: {resp.text[:60]}")
            except Exception as e:
                print(f"Groq Key {key_idx} exception: {e}")

        # 2. SECONDARY: Try Gemini if Groq keys fail or hit limit
        if settings.GEMINI_API_KEY:
            try:
                import httpx
                for m in ["gemini-flash-latest", "gemini-2.0-flash", "gemini-1.5-flash"]:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={settings.GEMINI_API_KEY}"
                    with httpx.Client(timeout=4.0) as client:
                        resp = client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                if text.strip():
                                    return text.strip().replace("\n", " ").replace('"', '')
            except Exception:
                pass

        # 3. TERTIARY: Try OpenAI if configured
        if settings.OPENAI_API_KEY:
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an insurance query optimizer. Output ONLY 4-7 space-separated legal/contract terms."},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=40,
                    temperature=0.1,
                    timeout=4.0
                )
                return resp.choices[0].message.content.strip()
            except Exception:
                pass

        return ""

    def process_query(self, query: str, active_policy_ids: List[str] = None) -> Dict[str, Any]:
        """Analyzes query and produces expanded query string with detected intent."""
        lower = query.lower()
        
        # 1. Intent Detection
        intent = "GENERAL"
        if any(w in lower for w in ["compare", "comparison", "difference", "versus", "vs", "which is better"]):
            intent = "POLICY_COMPARISON"
        elif any(w in lower for w in ["claim", "admissibility", "eligible for claim", "hospital bill", "deluxe room"]):
            intent = "CLAIMS_CALCULATION"
        elif any(w in lower for w in ["waiting period", "how long", "moratorium", "when can i claim", "wait"]):
            intent = "WAITING_PERIOD_CHECK"
        elif any(w in lower for w in ["exclude", "excluded", "not covered", "exclusion", "permanent exclusion"]):
            intent = "EXCLUSION_CHECK"
        elif any(w in lower for w in ["cover", "covered", "coverage", "pay for", "eligible"]):
            intent = "COVERAGE_CHECK"
        elif any(w in lower for w in ["what is", "meaning", "definition", "define", "explain"]):
            intent = "DEFINITION"
            
        # 2. Medical & Contractual Expansion
        expansions = []
        from backend.app.retrieval.medical_ontology import InsuranceMedicalOntology
        ontology_expansion = InsuranceMedicalOntology.get_query_expansion(query)
        medical_match = InsuranceMedicalOntology.match_condition(query)
        is_ped = medical_match and medical_match.get("type") == "PED"

        # PRIMARY: Run dynamic LLM Query Expander on EVERY incoming user query
        dyn_terms = self.get_dynamic_llm_expansion(query)
        if dyn_terms:
            expansions.append(dyn_terms)

        # REINFORCEMENT & FALLBACK: Combine with ontological contract codes
        if ontology_expansion:
            expansions.append(ontology_expansion)

        for term, replacement in self.EXPANSION_RULES.items():
            if re.search(r"\b" + re.escape(term) + r"\b", lower):
                # If query is about a specific PED condition (e.g. diabetes), do NOT pollute with 'specific disease 24 months'
                if is_ped and term == "waiting period":
                    expansions.append("pre-existing disease waiting period continuous coverage 36 months")
                else:
                    expansions.append(replacement)

        expanded_query = query
        if expansions:
            expanded_query = f"{query} {' '.join(expansions)}"
            
        return {
            "original_query": query,
            "expanded_query": expanded_query,
            "intent": intent,
            "medical_condition": medical_match,
            "active_policy_ids": active_policy_ids or []
        }
