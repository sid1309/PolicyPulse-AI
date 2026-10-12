from typing import List, Dict, Any, Optional
from backend.app.core.config import settings

class GraphRAGClient:
    """
    Manages Knowledge Graph relationships for insurance policies.
    Connects to Neo4j if available, with in-memory graph fallback for zero-dependency execution.
    """

    def __init__(self):
        self.driver = None
        self.is_neo4j_active = False
        self.in_memory_graph: Dict[str, Dict[str, Any]] = {}
        self._init_connection()

    def _init_connection(self):
        if settings.NEO4J_ENABLED:
            try:
                from neo4j import GraphDatabase
                self.driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                self.driver.verify_connectivity()
                self.is_neo4j_active = True
                print("Neo4j Knowledge Graph connected successfully.")
            except Exception as e:
                print(f"Notice: Neo4j not reachable ({e}). Using In-Memory Knowledge Graph.")
                self.is_neo4j_active = False

    def add_clause_relation(
        self,
        policy_id: str,
        clause_id: str,
        section_name: str,
        page_num: int,
        treatment: Optional[str] = None,
        waiting_period_months: Optional[int] = None,
        sublimit_text: Optional[str] = None
    ):
        """Adds nodes and relationships to knowledge graph."""
        if self.is_neo4j_active and self.driver:
            try:
                with self.driver.session() as session:
                    cypher = """
                    MERGE (p:Policy {id: $policy_id})
                    MERGE (c:Clause {id: $clause_id, policy_id: $policy_id, section: $section_name, page: $page_num})
                    MERGE (p)-[:HAS_CLAUSE]->(c)
                    """
                    session.run(cypher, policy_id=policy_id, clause_id=clause_id, section_name=section_name, page_num=page_num)
                    
                    if treatment:
                        session.run("""
                        MATCH (c:Clause {id: $clause_id, policy_id: $policy_id})
                        MERGE (t:Treatment {name: $treatment})
                        MERGE (c)-[:GOVERNS]->(t)
                        """, clause_id=clause_id, policy_id=policy_id, treatment=treatment.lower())
                        
                    if waiting_period_months:
                        session.run("""
                        MATCH (c:Clause {id: $clause_id, policy_id: $policy_id})
                        MERGE (w:WaitingPeriod {duration_months: $months})
                        MERGE (c)-[:SUBJECT_TO]->(w)
                        """, clause_id=clause_id, policy_id=policy_id, months=waiting_period_months)
            except Exception as e:
                print(f"Neo4j write error: {e}")
                
        # Also maintain in in-memory graph
        node_key = f"{policy_id}::{clause_id}"
        self.in_memory_graph[node_key] = {
            "policy_id": policy_id,
            "clause_id": clause_id,
            "section": section_name,
            "page": page_num,
            "treatment": treatment.lower() if treatment else None,
            "waiting_period_months": waiting_period_months,
            "sublimit": sublimit_text
        }

    def query_treatment_rules(self, policy_id: str, treatment_name: str) -> List[Dict[str, Any]]:
        """Finds multi-hop rules connecting a policy and treatment."""
        t_clean = treatment_name.lower().strip()
        
        # 1. Query Neo4j if active
        if self.is_neo4j_active and self.driver:
            try:
                with self.driver.session() as session:
                    res = session.run("""
                    MATCH (p:Policy {id: $policy_id})-[:HAS_CLAUSE]->(c:Clause)-[:GOVERNS]->(t:Treatment)
                    WHERE t.name CONTAINS $treatment
                    OPTIONAL MATCH (c)-[:SUBJECT_TO]->(w:WaitingPeriod)
                    RETURN c.id AS clause_id, c.section AS section, c.page AS page, w.duration_months AS waiting_months
                    """, policy_id=policy_id, treatment=t_clean)
                    records = [r.data() for r in res]
                    if records:
                        return records
            except Exception as e:
                print(f"Neo4j query error: {e}")
                
        # 2. In-Memory Graph Query
        matches = []
        for key, node in self.in_memory_graph.items():
            if node["policy_id"] == policy_id:
                if node.get("treatment") and t_clean in node["treatment"]:
                    matches.append({
                        "clause_id": node["clause_id"],
                        "section": node["section"],
                        "page": node["page"],
                        "waiting_months": node.get("waiting_period_months")
                    })
        return matches

    def close(self):
        if self.driver:
            self.driver.close()
