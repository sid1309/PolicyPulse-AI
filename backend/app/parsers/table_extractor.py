import pdfplumber
from typing import List, Dict, Any, Optional
from pathlib import Path

TABLE_CLASSIFICATIONS = {
    "MEDICAL_BENEFITS": {
        "keywords": ["sum insured", "room rent", "icu", "cataract", "sub-limit", 
                     "coverage", "benefit", "day care", "ambulance", "maternity",
                     "co-pay", "deductible", "waiting period", "robotic", "modern treatment"],
        "section_prefix": "Benefits & Sub-limits Grid"
    },
    "NON_PAYABLE_ITEMS": {
        "keywords": ["hand wash", "shoe cover", "comb", "gown", "slipper", "tissue",
                     "tooth paste", "tooth brush", "bed pan", "face mask", "room freshner",
                     "admission kit", "blanket", "cap", "cradle", "eau-de-cologne",
                     "hvac", "housekeeping", "luxury tax", "clean sheet", "schedule iii"],
        "section_prefix": "Non-Payable Items (Schedule III)"
    },
    "OMBUDSMAN_DIRECTORY": {
        "keywords": ["ombudsman", "bimalokpal", "grievance", "ernakulam", "guwahati",
                     "hyderabad", "jaipur", "insurance ombudsman", "tel.", "fax", "bhubaneswar"],
        "section_prefix": "Grievance Redressal / Ombudsman Directory"
    },
    "CLAIM_PROCEDURE": {
        "keywords": ["claim", "reimbursement", "time limit", "prescribed", "documentation",
                     "cashless", "pre-authorization"],
        "section_prefix": "Claim Filing Timelines & Procedures"
    },
    "DAY_CARE_PROCEDURES": {
        "keywords": ["day care", "procedure list", "annexure", "surgery list", "ent", "ophthalmology"],
        "section_prefix": "Day Care Procedure List"
    }
}

class TableExtractor:
    """
    Extracts tabular data from insurance policies (Day Care schedules, 
    Waiting Period grids, Room Rent limits) into Markdown and structured objects.
    """

    def _classify_table(self, headers: List[str], rows: List[List[str]]) -> tuple:
        """Classifies a table into a semantic category based on content inspection."""
        all_text = (" ".join(headers) + " " + " ".join([cell for row in rows for cell in row])).lower()
        
        best_category = "GENERAL_TABLE"
        best_score = 0
        for category, config in TABLE_CLASSIFICATIONS.items():
            score = sum(1 for kw in config["keywords"] if kw in all_text)
            if score > best_score:
                best_score = score
                best_category = category
        
        section_prefix = TABLE_CLASSIFICATIONS.get(best_category, {}).get("section_prefix", "Tabular Schedules / Sub-limits")
        return best_category, section_prefix

    def extract_tables_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        extracted_tables = []
        import gc
        try:
            with pdfplumber.open(file_path) as pdf:
                # Cap table extraction to 35 key pages to guarantee Render 512MB RAM compliance
                total_pages = len(pdf.pages)
                pages_to_check = pdf.pages[:35] if total_pages > 35 else pdf.pages

                for page_idx, page in enumerate(pages_to_check):
                    page_num = page_idx + 1
                    try:
                        tables = page.extract_tables()
                    except Exception:
                        tables = []
                    
                    for t_idx, table in enumerate(tables):
                        if not table or len(table) < 2:
                            continue
                            
                        # Clean cell values
                        cleaned_table = []
                        for row in table:
                            cleaned_row = [
                                str(cell).replace("\n", " ").strip() if cell is not None else ""
                                for cell in row
                            ]
                            # Only keep if row has at least one non-empty cell
                            if any(cleaned_row):
                                cleaned_table.append(cleaned_row)
                                
                        if len(cleaned_table) < 2:
                            continue
                            
                        headers = cleaned_table[0]
                        rows = cleaned_table[1:]
                        
                        # Generate clean Markdown representation
                        md_table = self._to_markdown(headers, rows)
                        category, section_prefix = self._classify_table(headers, rows)
                        
                        extracted_tables.append({
                            "table_id": f"p{page_num}_tbl{t_idx+1}",
                            "page_number": page_num,
                            "category": category,
                            "section_prefix": section_prefix,
                            "headers": headers,
                            "rows": rows,
                            "markdown": md_table,
                            "row_count": len(rows),
                            "col_count": len(headers)
                        })
                    
                    # Flush page layout cache immediately to release memory
                    try:
                        page.flush_cache()
                    except Exception:
                        pass
        except Exception as e:
            # Fallback gracefully if pdfplumber encounters non-standard font encoding
            print(f"Notice: Table extraction encountered issue: {e}")
        finally:
            gc.collect()
            
        return extracted_tables

    def _to_markdown(self, headers: List[str], rows: List[List[str]]) -> str:
        """Converts headers and rows to a GitHub-flavored Markdown table string."""
        col_count = len(headers)
        if col_count == 0:
            return ""
            
        # Pad shorter rows if any
        normalized_headers = [h if h else f"Col_{i+1}" for i, h in enumerate(headers)]
        header_line = "| " + " | ".join(normalized_headers) + " |"
        sep_line = "| " + " | ".join(["---"] * col_count) + " |"
        
        row_lines = []
        for row in rows:
            padded_row = (row + [""] * col_count)[:col_count]
            row_lines.append("| " + " | ".join(padded_row) + " |")
            
        return "\n".join([header_line, sep_line] + row_lines)
