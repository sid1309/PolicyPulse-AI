import re
import pymupdf as fitz  # PyMuPDF modern import
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

class LayoutParser:
    """
    Parses insurance policy PDFs preserving typographic hierarchy, 
    headings, clauses, page numbers, and coordinate bounding boxes.
    """

    def __init__(self):
        # Common section heading patterns in health insurance contracts
        self.section_patterns = [
            re.compile(r"^(SECTION|PART)\s+[0-9IVXLC]+[\.\:\s\-]*(.+)", re.IGNORECASE),
            re.compile(r"^([0-9]+\.[0-9]*)\s+([A-Z][A-Za-z\s\(\)\/\-]+)$"),
            re.compile(r"^([0-9]+)\s+(WAITING PERIODS?|EXCLUSIONS?|BENEFITS|SCOPE OF COVER|DEFINITIONS)", re.IGNORECASE),
            re.compile(r"^(DEFINITIONS|SCOPE OF COVER|BENEFITS|EXCLUSIONS|WAITING PERIODS?|GENERAL CONDITIONS|CLAIM PROCEDURE|GRIEVANCE REDRESSAL)", re.IGNORECASE),
            re.compile(r"Pre-Existing\s*Diseases?\s*\(Code[\-\s]*Excl01\)", re.IGNORECASE),
            re.compile(r"Specified\s*disease[\w\s/]*waiting\s*period[\-\s]*Code[\-\s]*Excl02", re.IGNORECASE),
            re.compile(r"30[\-\s]*day\s*waiting\s*period[\-\s]*Code[\-\s]*Excl03", re.IGNORECASE)
        ]
        
        # Clause / Sub-clause enumeration patterns
        self.clause_patterns = [
            re.compile(r"^([a-z]\))\s*(.*)", re.IGNORECASE),
            re.compile(r"^(\([a-z0-9]+\))\s*(.*)", re.IGNORECASE),
            re.compile(r"^([0-9]+\.[0-9]+(\.[0-9]+)?)\s*(.*)"),
            re.compile(r"^([ivxlcdm]+\.)\s*(.*)", re.IGNORECASE)
        ]

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extracts pages, text blocks with bounding boxes and font metadata.
        """
        doc = fitz.open(file_path)
        total_pages = len(doc)
        pages_data = []

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1
            rect = page.rect
            page_height = rect.height
            page_width = rect.width
            
            # Extract structured blocks with text and font sizes
            text_instances = page.get_text("dict", flags=fitz.TEXT_DEHYPHENATE)
            blocks = text_instances.get("blocks", [])
            
            parsed_blocks = []
            for b_idx, block in enumerate(blocks):
                if block.get("type") == 0:  # Text block
                    bbox = block.get("bbox") # [x0, y0, x1, y1]
                    
                    # Ignore running headers (top 5%) and footers (bottom 5%)
                    if bbox[1] < page_height * 0.05 or bbox[3] > page_height * 0.95:
                        continue
                        
                    block_text_lines = []
                    max_font_size = 0.0
                    is_bold = False
                    
                    for line in block.get("lines", []):
                        line_text_parts = []
                        for span in line.get("spans", []):
                            txt = span.get("text", "").strip()
                            if txt:
                                line_text_parts.append(txt)
                                size = span.get("size", 10.0)
                                if size > max_font_size:
                                    max_font_size = size
                                flags = span.get("flags", 0)
                                if flags & 2 or "bold" in span.get("font", "").lower():
                                    is_bold = True
                        if line_text_parts:
                            block_text_lines.append(" ".join(line_text_parts))
                            
                    block_content = " ".join(block_text_lines).strip()
                    if block_content:
                        parsed_blocks.append({
                            "block_id": f"p{page_num}_b{b_idx}",
                            "page": page_num,
                            "bbox": bbox,
                            "text": block_content,
                            "font_size": round(max_font_size, 1),
                            "is_bold": is_bold,
                        })
                        
            pages_data.append({
                "page_number": page_num,
                "width": page_width,
                "height": page_height,
                "blocks": parsed_blocks
            })
            
        doc.close()
        return {
            "total_pages": total_pages,
            "pages": pages_data
        }

    def detect_hierarchy_and_sections(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Passes through extracted blocks to reconstruct document section hierarchy.
        """
        structured_sections = []
        current_section = "General Provisions"
        current_subsection = ""
        
        for p in pages_data:
            page_num = p["page_number"]
            for block in p["blocks"]:
                text = block["text"].strip()
                size = block["font_size"]
                bold = block["is_bold"]
                
                # Check for major section headings
                is_heading = False
                for pat in self.section_patterns:
                    match = pat.search(text)
                    if match and (size >= 10.5 or bold or "excl" in text.lower()):
                        current_section = text
                        current_subsection = ""
                        is_heading = True
                        break
                        
                if not is_heading:
                    # Check for explicit waiting period / exclusion subsections
                    if re.search(r"pre-existing diseases?.*excl01", text, re.I):
                        current_section = "Waiting Periods & Exclusions"
                        current_subsection = "Pre-Existing Diseases (Code- Excl01)"
                        is_heading = True
                    elif re.search(r"specified disease.*excl02", text, re.I):
                        current_section = "Waiting Periods & Exclusions"
                        current_subsection = "Specified Disease/Procedure Waiting Period (Code- Excl02)"
                        is_heading = True
                    elif re.search(r"30[\-\s]*day.*excl03", text, re.I):
                        current_section = "Waiting Periods & Exclusions"
                        current_subsection = "30-Day Initial Waiting Period (Code- Excl03)"
                        is_heading = True
                    elif size >= 10.5 and bold:
                        # Check for subsection
                        if re.match(r"^([0-9]+\.[0-9]+)\s+", text):
                            current_subsection = text
                        
                structured_sections.append({
                    "page_number": page_num,
                    "section": current_section,
                    "subsection": current_subsection,
                    "bbox": block["bbox"],
                    "text": text,
                    "font_size": size,
                    "is_bold": bold
                })
                
        return structured_sections
