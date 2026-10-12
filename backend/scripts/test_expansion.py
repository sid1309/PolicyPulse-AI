import httpx, os
from dotenv import load_dotenv

load_dotenv("backend/.env")
key = os.getenv("GEMINI_API_KEY")

for q in [
    "if my eye point increases and requires to buy glasses then is it covered",
    "if i get cold or fever is it covered medicines",
    "I have diabetes. Is it covered and when does the waiting period end?"
]:
    p = (
        f"You are an insurance policy search optimizer. Convert this user question into 4-7 specific contractual, legal, or medical keywords and potential section names (e.g. Exclusions, OPD, Inpatient, Waiting Periods, clause codes) to search within an insurance contract PDF.\n"
        f"Question: \"{q}\"\n"
        f"Output ONLY a space-separated string of search terms, no explanation."
    )
    r = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}",
        json={"contents": [{"parts": [{"text": p}]}]},
        timeout=15.0
    )
    if r.status_code == 200:
        ans = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"QUERY: {q}\nEXPANSION: {ans}\n")
    else:
        print(f"FAILED {r.status_code}: {r.text}")
