# PolicyPulse AI
### Enterprise Health Insurance Intelligence & Claims Decision-Support Platform

PolicyPulse AI is an advanced, production-grade AI platform designed to eliminate the complexity and ambiguity of health insurance policies. Built on a high-precision **Hybrid RAG architecture (Dense Vector Search + Sparse BM25 + Reciprocal Rank Fusion + Cross-Encoder Reranking)** combined with a **Deterministic Claims Settlement Math Engine**, PolicyPulse delivers instant, mathematically verifiable policy analysis with page-exact clause citations.

---

## Key Capabilities

### 1. Ask PolicyPulse (Hybrid RAG Engine)
* **Dual-Engine Retrieval**: Combines semantic embeddings (`BAAI/bge-large-en-v1.5` / `FastEmbed`) with lexical keyword retrieval (`rank-bm25`) tuned for complex Indian insurance terminology.
* **Medical Ontology Expansion**: Automatically expands queries to capture medical synonyms, day-care procedures, surgical exclusions, and ICD classifications.
* **Reciprocal Rank Fusion (RRF) & Reranking**: Re-scores top retrieval candidates to surface the most legally binding policy clauses.
* **Verifiable Citation Linker**: Every answer links directly to exact clause numbers, policy headings, and page references—eliminating hallucinations.
* **Multi-Provider Failover**: Native support for **Groq** (`qwen/qwen3.8-27b`) and **Google Gemini** with automatic fallback.

### 2. Claims Settlement Math Engine
* **Deterministic Calculations**: Bypasses LLM hallucinations by calculating claim settlements through a rule-based deterministic arithmetic engine.
* **Multi-Stage Adjudication**:
  1. Deductible & non-payable expense deductions (consumables, registration fees).
  2. Room rent capping & proportional deduction penalties on associated medical expenses.
  3. Co-payment percentage deductions (age-based and zone-based).
  4. Specific illness sub-limits (e.g., Cataract, Joint Replacement).
  5. Sum Insured & Cumulative Bonus capping.
* **Complete Audit Trail**: Generates a step-by-step mathematical breakdown suitable for policyholders and claims adjusters.

### 3. Policy Comparison & Semantic Diff Engine
* **Side-by-Side Benefit Matrix**: Compares up to 3 policies simultaneously across room rent caps, ICU limits, pre-existing disease (PED) waiting periods, co-pay rules, day care covers, and modern treatment restoration.
* **Policy Diff View**: Analyzes revisions between different policy years (e.g., 2021 vs. 2024 policy wordings) to pinpoint subtle clause alterations, benefit exclusions, or added sub-limits.

### 4. Ingestion & Policy Management
* **Layout-Aware PDF Ingestion**: Extracts tables, headings, footnotes, and multi-column policy text using `PyMuPDF` and `pdfplumber`.
* **In-App PDF Viewer**: View the original insurer policy documents with source clause highlights directly in the browser.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Lucide Icons, Vanilla CSS |
| **Backend API** | FastAPI, Uvicorn, Pydantic V2 |
| **Vector & Search** | Qdrant Client, Rank-BM25, FastEmbed, Sentence-Transformers |
| **PDF Extraction** | PyMuPDF (fitz), pdfplumber |
| **AI / LLMs** | Google Gemini (`gemini-3.8-flash`), Groq (`qwen/qwen3.8-27b`) |
| **Math Engine** | Custom deterministic Python claims adjudication pipeline |

---

## License
This project is licensed under the MIT License.
