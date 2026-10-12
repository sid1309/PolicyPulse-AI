import re
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.app.core.models import ClauseChunk
from backend.app.parsers.layout_parser import LayoutParser
from backend.app.parsers.table_extractor import TableExtractor

class StructureAwareChunker:
    """
    Structure-aware chunker that groups text into legal clauses, 
    preserving hierarchical breadcrumb paths, table integrity, and normalized entity metadata.
    """

    COMMON_TREATMENTS = [
        "cataract", "hernia", "hydrocele", "fistula", "piles", "hemorrhoids",
        "joint replacement", "knee replacement", "hip replacement",
        "calculi", "kidney stone", "urinary stone", "gall bladder", "cholecystectomy",
        "hysterectomy", "fibroid", "endometriosis", "prostate", "bph",
        "benign prostatic hypertrophy", "sinusitis", "tonsillectomy",
        "chemotherapy", "radiotherapy", "dialysis", "robotic surgery",
        "bariatric surgery", "dental", "cosmetic", "maternity", "ayush"
    ]

    def __init__(self):
        self.layout_parser = LayoutParser()
        self.table_extractor = TableExtractor()

    def chunk_policy(
        self,
        file_path: str,
        policy_id: str,
        insurer: str = "Standard Insurer",
        plan_name: str = "Health Plan",
        version: str = "2024"
    ) -> List[ClauseChunk]:
        """
        Parses policy PDF and produces structured ClauseChunk objects.
        """
        # 1. Parse layout & blocks
        pdf_data = self.layout_parser.parse_pdf(file_path)
        sections_data = self.layout_parser.detect_hierarchy_and_sections(pdf_data["pages"])
        
        # 2. Extract tables
        tables = self.table_extractor.extract_tables_from_pdf(file_path)
        table_page_map = {}
        for tbl in tables:
            pg = tbl["page_number"]
            table_page_map.setdefault(pg, []).append(tbl)
            
        chunks: List[ClauseChunk] = []
        
        # 3. Aggregate text blocks into cohesive clause chunks
        current_chunk_blocks = []
        current_section = "General Provisions"
        current_subsection = ""
        current_clause_title = ""
        current_page = 1
        current_bboxes = []
        
        clause_start_re = re.compile(
            r"^(([a-z0-9]\))\s*|([0-9]+(\.[0-9]+)*[\.\)]\s*)|([ivxlcdm]+[\.\)]\s*)|(Def\s+[0-9]+[\.\:]\s*)|(Definition\s+[0-9]+[\.\:]\s*))",
            re.IGNORECASE
        )

        for block in sections_data:
            block_text = block["text"]
            page_num = block["page_number"]
            sec = block["section"]
            subsec = block["subsection"]
            bbox = block["bbox"]
            
            # Detect boundary: change of section OR start of a new enumerated clause OR explicit exclusion code
            is_excl_heading = bool(re.search(r"Code[\-\s]*Excl[0-9]+|Pre-Existing\s*Diseases?|Waiting\s*Period", block_text, re.I))
            is_new_clause = bool(clause_start_re.match(block_text)) or is_excl_heading
            is_new_section = (sec != current_section or (subsec and subsec != current_subsection))
            
            # If we accumulated sufficient text and hit a boundary, flush current chunk
            # Avoid flushing isolated heading stubs (< 80 chars)
            accumulated_len = sum(len(b) for b in current_chunk_blocks)
            if current_chunk_blocks and (is_new_clause or is_new_section) and (accumulated_len >= 80 or is_new_section):
                chunk_obj = self._create_chunk(
                    policy_id=policy_id,
                    insurer=insurer,
                    plan_name=plan_name,
                    version=version,
                    section=current_section,
                    clause_title=current_clause_title or current_subsection or current_section,
                    page_num=current_page,
                    blocks=current_chunk_blocks,
                    bboxes=current_bboxes
                )
                if chunk_obj:
                    chunks.append(chunk_obj)
                    
                current_chunk_blocks = []
                current_bboxes = []
                
            current_section = sec
            current_subsection = subsec
            current_page = page_num
            if is_new_clause:
                if re.search(r"pre-existing diseases?.*excl01|excl01.*pre-existing", block_text, re.I):
                    current_clause_title = "Pre-Existing Diseases (Code- Excl01)"
                    current_section = "Waiting Periods & Exclusions"
                elif re.search(r"specified disease.*excl02|excl02.*specified disease", block_text, re.I):
                    current_clause_title = "Specified Disease/Procedure Waiting Period (Code- Excl02)"
                    current_section = "Waiting Periods & Exclusions"
                elif re.search(r"30[\-\s]*day.*excl03|excl03.*30[\-\s]*day", block_text, re.I):
                    current_clause_title = "30-Day Initial Waiting Period (Code- Excl03)"
                    current_section = "Waiting Periods & Exclusions"
                else:
                    match = clause_start_re.match(block_text)
                    enum_prefix = match.group(0).strip() if match else ""
                    rest_of_text = block_text[len(enum_prefix):].strip()
                    
                    # Check if first line/phrase has a colon, dash, or newline indicating a named clause title
                    first_line = rest_of_text.split("\n")[0].strip()
                    title_candidate = ""
                    if ":" in first_line:
                        title_candidate = first_line.split(":")[0].strip()
                    elif " - " in first_line or " – " in first_line:
                        title_candidate = re.split(r" [-–] ", first_line)[0].strip()
                    elif len(first_line) <= 55 and not first_line.endswith("."):
                        title_candidate = first_line
                        
                    if title_candidate and len(title_candidate) >= 3 and len(title_candidate) <= 65:
                        current_clause_title = f"{enum_prefix} {title_candidate}".strip()
                    elif subsec:
                        current_clause_title = f"{subsec} ({enum_prefix})" if enum_prefix else subsec
                    elif enum_prefix:
                        current_clause_title = f"{enum_prefix} {first_line[:40]}".strip()
                    else:
                        current_clause_title = sec
                
            current_chunk_blocks.append(block_text)
            if bbox:
                current_bboxes.append(bbox)

        # Flush final chunk
        if current_chunk_blocks:
            chunk_obj = self._create_chunk(
                policy_id=policy_id,
                insurer=insurer,
                plan_name=plan_name,
                version=version,
                section=current_section,
                clause_title=current_clause_title or current_subsection or current_section,
                page_num=current_page,
                blocks=current_chunk_blocks,
                bboxes=current_bboxes
            )
            if chunk_obj:
                chunks.append(chunk_obj)
                
        # 4. Add Table chunks with structured Markdown and semantic classification
        for tbl in tables:
            tbl_page = tbl["page_number"]
            category = tbl.get("category", "GENERAL_TABLE")
            table_section = tbl.get("section_prefix", "Tabular Schedules / Sub-limits")
            
            if category == "MEDICAL_BENEFITS":
                clause_title = f"Medical Benefits & Sub-limits Grid (Page {tbl_page})"
            elif category == "NON_PAYABLE_ITEMS":
                clause_title = f"Non-Payable Consumables Schedule (Page {tbl_page})"
            elif category == "OMBUDSMAN_DIRECTORY":
                clause_title = f"Ombudsman & Grievance Directory (Page {tbl_page})"
            elif category == "CLAIM_PROCEDURE":
                clause_title = f"Claim Timelines & Documents Grid (Page {tbl_page})"
            elif category == "DAY_CARE_PROCEDURES":
                clause_title = f"Day Care Procedures Annexure (Page {tbl_page})"
            else:
                clause_title = f"Table Schedule (Page {tbl_page})"

            tbl_text = (
                f"[Policy: {insurer} - {plan_name}] > [{table_section}] > [{clause_title}]:\n\n"
                f"{tbl['markdown']}"
            )
            tbl_chunk = ClauseChunk(
                chunk_id=str(uuid.uuid4()),
                policy_id=policy_id,
                insurer=insurer,
                plan_name=plan_name,
                version=version,
                section_name=table_section,
                clause_id=tbl["table_id"],
                clause_title=clause_title,
                page_number=tbl_page,
                page_range=[tbl_page],
                chunk_type="table",
                content_text=tbl_text,
                entities=self._extract_entities(tbl_text)
            )
            chunks.append(tbl_chunk)
            
        return chunks

    def _create_chunk(
        self,
        policy_id: str,
        insurer: str,
        plan_name: str,
        version: str,
        section: str,
        clause_title: str,
        page_num: int,
        blocks: List[str],
        bboxes: List[List[float]]
    ) -> Optional[ClauseChunk]:
        # Smart formatting: insert line breaks before numbered subpoints (1., 2., a), etc.)
        joined_text = " ".join(blocks).strip()
        # 1. Break list-starter (1. / a)) after any non-whitespace characters (like Code- Excl02 or heading titles)
        formatted_text = re.sub(r'(?<!\n)(?<=\S)\s+([1a]\.\s+|[1a]\)\s+|\([1a]\)\s+)', r'\n\n\1', joined_text)
        # 2. Break subsequent list points (2., 3., b), c)) following punctuation
        formatted_text = re.sub(r'([;\.\:])\s+(\b[0-9]{1,2}\.|\b[a-z0-9]\)|\b[ivxlcdm]+\.)\s+', r'\1\n\n\2 ', formatted_text)
        # 3. Break before exclusion codes
        formatted_text = re.sub(r'([;\.\:\)])\s+(Code[\-\s]*Excl[0-9]+|\bExcl[0-9]+\b)', r'\1\n\n\2', formatted_text, flags=re.I)
        # 4. Break definitions (Def 13., Def 14., Definition 15., etc.) onto newlines
        formatted_text = re.sub(r'(?<!\n)(?<=\S)\s+(Def\s+[0-9]+[\.\:]|\bDefinition\s+[0-9]+[\.\:])', r'\n\n\1', formatted_text, flags=re.I)
        raw_text = formatted_text

        if len(raw_text) < 25:  # Skip trivial snippets
            return None
            
        breadcrumb = f"[{insurer} - {plan_name}] > [{section}] > [{clause_title}]:\n"
        full_content = breadcrumb + raw_text
        
        # Merge bounding box to cover the clause region
        merged_bbox = None
        if bboxes:
            x0 = min(b[0] for b in bboxes)
            y0 = min(b[1] for b in bboxes)
            x1 = max(b[2] for b in bboxes)
            y1 = max(b[3] for b in bboxes)
            merged_bbox = [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)]
            
        entities = self._extract_entities(raw_text)
        
        return ClauseChunk(
            chunk_id=str(uuid.uuid4()),
            policy_id=policy_id,
            insurer=insurer,
            plan_name=plan_name,
            version=version,
            section_name=section,
            clause_id=clause_title[:40],
            clause_title=clause_title,
            page_number=page_num,
            page_range=[page_num],
            chunk_type="clause",
            content_text=full_content,
            bbox=merged_bbox,
            entities=entities
        )

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extracts normalized insurance entities from chunk text."""
        lower = text.lower()
        entities: Dict[str, Any] = {
            "treatments": [],
            "waiting_period_months": None,
            "room_rent_cap": None,
            "copay_percent": None
        }
        
        # Detect treatments
        for t in self.COMMON_TREATMENTS:
            if t in lower:
                entities["treatments"].append(t)
                
        # Detect waiting periods (must explicitly mention waiting period; max 48 months)
        wp_match = re.search(r"(\b[0-9]{1,2}\b)\s*(months?|years?)\s*(?:initial\s*|ped\s*|specific\s*)?waiting\s*period", lower)
        if not wp_match:
            wp_match = re.search(r"waiting\s*period\s*(?:of\s*)?(\b[0-9]{1,2}\b)\s*(months?|years?)", lower)
        if wp_match:
            num = int(wp_match.group(1))
            unit = wp_match.group(2)
            if "year" in unit:
                num *= 12
            if 1 <= num <= 48:
                entities["waiting_period_months"] = num
            
        # Detect co-pay (e.g. 10% co-payment, 20% co-pay)
        copay_match = re.search(r"(\b[0-9]{1,2}\b)%\s*(co[\-\s]?pay|co[\-\s]?payment)", lower)
        if copay_match:
            entities["copay_percent"] = int(copay_match.group(1))
            
        # Detect room rent caps
        if "single private room" in lower:
            entities["room_rent_cap"] = "Single Private Room"
        elif "no room rent capping" in lower or "no capping on room rent" in lower:
            entities["room_rent_cap"] = "No Capping"
        else:
            rr_pct = re.search(r"([0-9\.]+)%\s*of\s*(?:the\s*)?sum\s*insured(?:\s*per\s*day)?", lower)
            icu_pct = re.search(r"icu[^\.]*?([0-9\.]+)%\s*of\s*(?:the\s*)?sum\s*insured", lower)
            if rr_pct and icu_pct:
                entities["room_rent_cap"] = f"{rr_pct.group(1)}% of Sum Insured / Day (ICU: {icu_pct.group(1)}% / Day)"
            elif rr_pct:
                entities["room_rent_cap"] = f"{rr_pct.group(1)}% of Sum Insured per day"
                
        return entities
