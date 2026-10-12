import re
from typing import Dict, Any, Optional, List, Tuple

class InsuranceMedicalOntology:
    """
    Ontological knowledge base linking clinical disease names and layman symptoms
    to contractual IRDAI health insurance clauses, legal exclusion codes, and waiting periods.
    """

    PED_CONDITIONS = {
        "diabetes": {"name": "Diabetes Mellitus", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "diabetic": {"name": "Diabetes Mellitus", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "sugar": {"name": "Diabetes Mellitus", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "type 1": {"name": "Type 1 Diabetes", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "type 2": {"name": "Type 2 Diabetes", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "insulin": {"name": "Diabetes (Insulin-dependent)", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "hypertension": {"name": "Hypertension (High BP)", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "high bp": {"name": "Hypertension", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "blood pressure": {"name": "Hypertension", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "bp": {"name": "Hypertension", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "thyroid": {"name": "Thyroid Disorder", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "hypothyroidism": {"name": "Hypothyroidism", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "hyperthyroidism": {"name": "Hyperthyroidism", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "asthma": {"name": "Bronchial Asthma", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "copd": {"name": "COPD", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "heart disease": {"name": "Cardiovascular / Heart Disease", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "cad": {"name": "Coronary Artery Disease", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "cholesterol": {"name": "Dyslipidemia", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "kidney disease": {"name": "Chronic Kidney Disease", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "ckd": {"name": "Chronic Kidney Disease", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "pre-existing": {"name": "Pre-Existing Disease", "type": "PED", "code": "Excl01", "std_wait_months": 36},
        "ped": {"name": "Pre-Existing Disease", "type": "PED", "code": "Excl01", "std_wait_months": 36}
    }

    SPECIFIED_PROCEDURES = {
        "cataract": {"name": "Cataract Surgery", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24, "has_sublimit": True},
        "eye surgery": {"name": "Cataract & Eye Procedures", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "hernia": {"name": "Hernia of all types", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "hydrocele": {"name": "Hydrocele", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "piles": {"name": "Piles / Hemorrhoids", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "fistula": {"name": "Fistula in Ano", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "fissure": {"name": "Fissure in Ano", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "kidney stone": {"name": "Renal / Kidney Calculi", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "gall stone": {"name": "Gall Bladder Calculi / Cholelithiasis", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "gallbladder": {"name": "Gall Bladder Calculi", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "hysterectomy": {"name": "Hysterectomy", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "fibroid": {"name": "Uterine Fibroids", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "prostate": {"name": "Benign Prostatic Hypertrophy (BPH)", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "bph": {"name": "Benign Prostatic Hypertrophy", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "knee replacement": {"name": "Joint Replacement (Knee)", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "joint replacement": {"name": "Joint Replacement", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "sinus": {"name": "Sinusitis & Pilonidal Sinus", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "sinusitis": {"name": "Sinusitis", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "tonsil": {"name": "Tonsillectomy", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "varicose": {"name": "Varicose Veins", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "slip disc": {"name": "Prolapsed Intervertebral Disc", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24},
        "sciatica": {"name": "Spinal & Disc Disorders", "type": "SPECIFIED", "code": "Excl02", "std_wait_months": 24}
    }

    MODERN_TREATMENTS = {
        "robotic": {"name": "Robotic Surgery", "type": "MODERN", "sublimit_pct": 50},
        "stem cell": {"name": "Stem Cell Therapy", "type": "MODERN", "sublimit_pct": 50},
        "immunotherapy": {"name": "Immunotherapy", "type": "MODERN", "sublimit_pct": 50},
        "chemotherapy": {"name": "Oral Chemotherapy", "type": "MODERN", "sublimit_pct": 50},
        "balloon sinuplasty": {"name": "Balloon Sinuplasty", "type": "MODERN", "sublimit_pct": 50},
        "deep brain stimulation": {"name": "Deep Brain Stimulation", "type": "MODERN", "sublimit_pct": 50}
    }

    EXCLUSION_CONDITIONS = {
        "bariatric": {"name": "Bariatric Surgery (Obesity / Weight Control)", "type": "EXCLUSION", "code": "Excl06"},
        "weight loss": {"name": "Obesity & Weight Control", "type": "EXCLUSION", "code": "Excl06"},
        "obesity": {"name": "Obesity / Weight Control", "type": "EXCLUSION", "code": "Excl06"},
        "unproven": {"name": "Unproven Treatments", "type": "EXCLUSION", "code": "Excl16"},
        "experimental": {"name": "Unproven / Experimental Treatments", "type": "EXCLUSION", "code": "Excl16"},
        "glasses": {"name": "Refractive Error (Spectacles)", "type": "EXCLUSION", "code": "Excl15"},
        "spectacles": {"name": "Refractive Error (Spectacles)", "type": "EXCLUSION", "code": "Excl15"},
        "cosmetic": {"name": "Cosmetic or Plastic Surgery", "type": "EXCLUSION", "code": "Excl08"},
        "alcoholism": {"name": "Treatment for Alcoholism & Substance Abuse", "type": "EXCLUSION", "code": "Excl12"},
        "adventure sports": {"name": "Hazardous or Adventure Sports", "type": "EXCLUSION", "code": "Excl09"},
        "breach of law": {"name": "Breach of Law with Criminal Intent", "type": "EXCLUSION", "code": "Excl10"}
    }

    SPECIAL_BENEFITS = {
        "organ donor": {"name": "Organ Donor Inpatient Hospitalization", "type": "BENEFIT", "section": "4.4 Organ Donor Expenses"},
        "donor": {"name": "Organ Donor Inpatient Hospitalization", "type": "BENEFIT", "section": "4.4 Organ Donor Expenses"},
        "ambulance": {"name": "Emergency Ground Ambulance", "type": "BENEFIT", "section": "4.5 Emergency Ground Ambulance"},
        "ayush": {"name": "AYUSH Hospitalization Treatment", "type": "BENEFIT", "section": "4.2 AYUSH Treatment"}
    }

    @classmethod
    def match_condition(cls, text: str) -> Optional[Dict[str, Any]]:
        """Matches clinical text to an ontological insurance classification."""
        lower = text.lower()
        
        # Check Exclusion conditions
        for key, info in cls.EXCLUSION_CONDITIONS.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower):
                return info

        # Check Special Benefits
        for key, info in cls.SPECIAL_BENEFITS.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower):
                return info

        # Check PED conditions first
        for key, info in cls.PED_CONDITIONS.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower):
                return info
                
        # Check Specified procedures
        for key, info in cls.SPECIFIED_PROCEDURES.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower):
                return info
                
        # Check Modern treatments
        for key, info in cls.MODERN_TREATMENTS.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower):
                return info
                
        return None

    @classmethod
    def get_query_expansion(cls, query: str) -> str:
        """
        Expands clinical queries with exact legal contract codes, sections, and search anchors.
        """
        match = cls.match_condition(query)
        if not match:
            return ""
            
        mtype = match.get("type")
        if mtype == "EXCLUSION":
            code = match.get("code", "")
            name = match.get("name", "")
            return f"standard exclusions {code} {name} permanent exclusion not payable 8.1"
        elif mtype == "BENEFIT":
            sec = match.get("section", "")
            name = match.get("name", "")
            return f"{sec} {name} Inpatient Hospitalization medical expenses covered Section 4"
        elif mtype == "PED":
            # Diabetes, BP, Thyroid, etc. MUST expand to Pre-Existing Diseases Excl01
            return "pre-existing disease PED Excl01 pre-existing diseases waiting period continuous coverage 36 months"
        elif mtype == "SPECIFIED":
            name = match.get("name")
            return f"specified disease procedure waiting period Excl02 24 months {name}"
        elif mtype == "MODERN":
            return "modern treatment methods 4.7 robotic surgeries 50% sum insured sublimit"
            
        return ""
