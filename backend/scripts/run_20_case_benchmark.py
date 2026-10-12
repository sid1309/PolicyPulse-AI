import json
import time
import urllib.request
from pathlib import Path

BACKEND_URL = "http://127.0.0.1:8000/api/chat"

TEST_SUITE = [
    {
        "id": "TC-01",
        "category": "Accidental Emergency",
        "question": "I had a bike accident and broke my leg, is hospital treatment covered?",
        "expected_verdict_category": "COVERED",
        "description": "Accidental injury hospitalization covered from Day 1 with 0 waiting period"
    },
    {
        "id": "TC-02",
        "category": "Outpatient / Minor Illness",
        "question": "If I get cold or fever, are medicines and doctor consultation covered?",
        "expected_verdict_category": "NOT COVERED",
        "description": "Routine outpatient / OPD consultation & pharmacy pills require 24h hospitalization"
    },
    {
        "id": "TC-03",
        "category": "Vision / Optical",
        "question": "My eye power increased and I need to buy prescription glasses, is it covered?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Spectacles / refractive error less than 7.5 dioptres is excluded under Code Excl15"
    },
    {
        "id": "TC-04",
        "category": "Specified Illness",
        "question": "Is cataract eye surgery covered and is there any waiting period or limit?",
        "expected_verdict_category": "CONDITIONALLY COVERED",
        "description": "Cataract surgery covered subject to 24-month waiting period and sub-limit per eye"
    },
    {
        "id": "TC-05",
        "category": "Dental",
        "question": "Can I claim for routine dental cavity filling and tooth extraction?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Dental treatment excluded under Def 13 unless due to accidental hospitalization"
    },
    {
        "id": "TC-06",
        "category": "Cosmetic Surgery",
        "question": "Is cosmetic nose reshaping rhinoplasty covered to improve appearance?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Cosmetic or plastic surgery excluded under Code Excl08 unless post-accident reconstruction"
    },
    {
        "id": "TC-07",
        "category": "Pre-Existing Diseases",
        "question": "I have type 2 diabetes and hypertension, when can I claim for related hospitalization?",
        "expected_verdict_category": "CONDITIONALLY COVERED",
        "description": "PED covered after mandatory Pre-Existing Disease waiting period (typically 36 months)"
    },
    {
        "id": "TC-08",
        "category": "Room Rent & ICU",
        "question": "If I take a luxury suite room above my eligible room rent, what deduction applies?",
        "expected_verdict_category": "SUBJECT TO ROOM RENT LIMIT",
        "description": "Proportionate deduction applies on all associated medical expenses for room tariff excess"
    },
    {
        "id": "TC-09",
        "category": "Modern Treatments",
        "question": "Does the policy pay for robotic surgery or modern treatment methods?",
        "expected_verdict_category": "COVERED",
        "description": "Modern treatments / robotic surgery covered up to defined sub-limits (e.g. 50% SI)"
    },
    {
        "id": "TC-10",
        "category": "AYUSH Inpatient",
        "question": "Is Ayurvedic or Homeopathy hospitalization treatment covered under this policy?",
        "expected_verdict_category": "COVERED",
        "description": "AYUSH treatment covered when taken in a recognized government/accredited hospital"
    },
    {
        "id": "TC-11",
        "category": "Ambulance",
        "question": "Are emergency road ambulance charges covered when shifting to hospital?",
        "expected_verdict_category": "COVERED",
        "description": "Emergency ground ambulance covered per hospitalization episode"
    },
    {
        "id": "TC-12",
        "category": "Day Care Treatments",
        "question": "Is chemotherapy or dialysis covered if discharge happens within 6 hours without 24h stay?",
        "expected_verdict_category": "COVERED",
        "description": "Day Care treatments covered under Section 4.3 without requiring 24-hour hospital stay"
    },
    {
        "id": "TC-13",
        "category": "Maternity",
        "question": "Are pregnancy delivery charges and childbirth expenses covered under the base policy?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Maternity expenses excluded under standard health insurance unless specialized rider active"
    },
    {
        "id": "TC-14",
        "category": "Bariatric Surgery",
        "question": "Is bariatric weight loss surgery covered under this health policy?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Bariatric surgery excluded under Code Excl06 unless life-threatening BMI > 40 criteria met"
    },
    {
        "id": "TC-15",
        "category": "Adventure Sports",
        "question": "If I get injured while participating in professional motor racing or skydiving, is it covered?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Hazardous or adventure sports as a professional excluded under Code Excl09"
    },
    {
        "id": "TC-16",
        "category": "Substance Abuse",
        "question": "Are rehabilitation expenses for alcohol or drug addiction covered?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Treatment for alcoholism and drug/substance abuse excluded under Code Excl12"
    },
    {
        "id": "TC-17",
        "category": "Unproven Treatments",
        "question": "Is experimental stem cell therapy with unproven medical efficacy covered?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Unproven treatments lacking medical documentation excluded under Code Excl16"
    },
    {
        "id": "TC-18",
        "category": "Breach of Law",
        "question": "Will insurance pay if injuries happen while committing a criminal breach of law?",
        "expected_verdict_category": "EXCLUDED",
        "description": "Breach of law with criminal intent excluded under Code Excl10"
    },
    {
        "id": "TC-19",
        "category": "Organ Donor",
        "question": "Are hospitalization expenses of an organ donor covered when donating an organ to me?",
        "expected_verdict_category": "COVERED",
        "description": "Organ donor medical expenses covered under Inpatient Care for harvesting organ"
    },
    {
        "id": "TC-20",
        "category": "Initial Waiting Period",
        "question": "Can I claim for viral pneumonia diagnosed on day 10 after buying the policy?",
        "expected_verdict_category": "CONDITIONALLY COVERED",
        "description": "30-day initial waiting period applies to all fresh illnesses under Code Excl03"
    }
]

def evaluate_verdict(actual_answer: str, expected_category: str) -> bool:
    ans_upper = actual_answer.upper()
    if expected_category == "COVERED":
        # Must contain covered but NOT "NOT COVERED" or "EXCLUDED"
        if "NOT COVERED" in ans_upper or "EXCLUDED" in ans_upper:
            return False
        return "COVERED" in ans_upper
    elif expected_category == "NOT COVERED":
        return "NOT COVERED" in ans_upper or "EXCLUDED" in ans_upper
    elif expected_category == "EXCLUDED":
        return "EXCLUDED" in ans_upper or "NOT COVERED" in ans_upper
    elif expected_category == "CONDITIONALLY COVERED":
        return "CONDITIONALLY COVERED" in ans_upper or "WAITING PERIOD" in ans_upper or "WAIT" in ans_upper
    elif expected_category == "SUBJECT TO ROOM RENT LIMIT":
        return "ROOM RENT" in ans_upper or "PROPORTIONATE" in ans_upper
    return False

def run_benchmark():
    print(f"=== Running 20-Case Comprehensive Benchmark against {BACKEND_URL} ===")
    results = []
    passed_count = 0
    
    for idx, test in enumerate(TEST_SUITE, 1):
        q = test["question"]
        print(f"\n[{idx}/20] Testing {test['id']} ({test['category']}):")
        print(f"     Q: \"{q}\"")
        
        t0 = time.time()
        try:
            req_data = json.dumps({"query": q}).encode("utf-8")
            req = urllib.request.Request(
                BACKEND_URL,
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as res:
                res_body = res.read().decode("utf-8")
                resp_json = json.loads(res_body)
        except Exception as e:
            print(f"     ERROR calling backend: {e}")
            results.append({
                **test,
                "status": "FAIL",
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "actual_verdict": f"ERROR: {e}",
                "actual_answer": "",
                "governing_section": "N/A",
                "clause_title": "N/A",
                "page_number": 0,
                "failure_reason": f"API request failed: {str(e)}"
            })
            continue

        latency_ms = round((time.time() - t0) * 1000, 1)
        answer = resp_json.get("answer", "")
        
        # Extract verdict line
        first_line = answer.split("\n")[0].strip() if answer else "N/A"
        citations = resp_json.get("citations", [])
        top_cit = citations[0] if citations else {}
        
        passed = evaluate_verdict(answer, test["expected_verdict_category"])
        if passed:
            passed_count += 1
            status = "PASS"
            failure_reason = ""
        else:
            status = "FAIL"
            failure_reason = f"Expected '{test['expected_verdict_category']}', but answer produced: '{first_line[:80]}'"

        print(f"     Status: {status} | Latency: {latency_ms}ms")
        print(f"     Verdict: {first_line[:70]}")
        print(f"     Clause: {top_cit.get('clause_title', 'N/A')} (Page {top_cit.get('page_number', 'N/A')})")

        results.append({
            **test,
            "status": status,
            "latency_ms": latency_ms,
            "actual_verdict": first_line,
            "actual_answer": answer[:350],
            "governing_section": top_cit.get("section_name", "N/A"),
            "clause_title": top_cit.get("clause_title", "N/A"),
            "page_number": top_cit.get("page_number", 0),
            "failure_reason": failure_reason
        })

    accuracy = round((passed_count / len(TEST_SUITE)) * 100, 1)
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": len(TEST_SUITE),
        "passed": passed_count,
        "failed": len(TEST_SUITE) - passed_count,
        "accuracy_pct": accuracy,
        "results": results
    }

    out_file = Path("backend/data/eval_20_benchmark_results.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n==========================================")
    print(f"Benchmark Complete! Accuracy: {passed_count}/{len(TEST_SUITE)} ({accuracy}%)")
    print(f"Results saved to: {out_file}")
    print(f"==========================================")

if __name__ == "__main__":
    run_benchmark()
