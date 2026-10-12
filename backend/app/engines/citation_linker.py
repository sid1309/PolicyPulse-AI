from typing import List, Dict, Any
from backend.app.core.models import CitationItem

class CitationLinker:
    """
    Constructs clean, verifiable citation items linked to exact 
    pages and PDF coordinate bounding boxes.
    """

    @staticmethod
    def create_citations_from_chunks(chunks: List[Dict[str, Any]]) -> List[CitationItem]:
        citations = []
        for c in chunks:
            text = c.get("content_text", "")
            # Extract first 250 characters as clean excerpt
            clean_excerpt = text.split("\n\n")[-1] if "\n\n" in text else text
            clean_excerpt = clean_excerpt[:280].strip() + ("..." if len(clean_excerpt) > 280 else "")
            
            citations.append(CitationItem(
                policy_id=c.get("policy_id", "Unknown Policy"),
                insurer=c.get("insurer", "Standard Insurer"),
                plan_name=c.get("plan_name", "Health Plan"),
                section_name=c.get("section_name", "General Provisions"),
                clause_id=str(c.get("clause_id", "Clause")),
                clause_title=c.get("clause_title", "Section Terms"),
                page_number=int(c.get("page_number", 1)),
                excerpt=clean_excerpt,
                bbox=c.get("bbox"),
                relevance_score=c.get("normalized_score") or c.get("rrf_score")
            ))
        return citations
