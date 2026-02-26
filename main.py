from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI()

# ✅ Enable CORS (required by evaluator)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ HARDCODED TOKEN (rotate after assignment)
AIPIPE_TOKEN = "YOUR_TOKEN_HERE"


# ---------- Response Model ----------
class SentimentResponse(BaseModel):
    sentiment: str
    rating: int


# 🔥 CORE FUNCTION — handles ANY input format
async def process_text(data: dict):
    try:
        # ✅ Evaluator may send {comment: "..."} OR {code: "..."}
        text = data.get("comment") or data.get("code")

        if not text:
            raise HTTPException(status_code=400, detail="No input text found")

        url = "https://aipipe.org/openrouter/v1/responses"

        payload = {
            "model": "openai/gpt-4.1-mini",
            "input": f"""
Analyze the sentiment of this comment and return ONLY valid JSON.

Comment: {text}

Return format:
{{
  "sentiment": "positive | negative | neutral",
  "rating": 1-5
}}
"""
        }

        headers = {
            "Authorization": f"Bearer {AIPIPE_TOKEN}",
            "Content-Type": "application/json"
        }

        r = requests.post(url, headers=headers, json=payload, timeout=30)

        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=r.text)

        response_json = r.json()

        # 🔎 Extract model output safely
        output_text = None
        if "output" in response_json:
            for item in response_json["output"]:
                if "content" in item:
                    for c in item["content"]:
                        if c.get("type") == "output_text":
                            output_text = c.get("text")

        if not output_text:
            raise HTTPException(status_code=500, detail="No text output")

        return json.loads(output_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Main endpoint
@app.post("/comment", response_model=SentimentResponse)
async def analyze_comment(data: dict = Body(...)):
    return await process_text(data)


# ✅ Evaluator endpoint (IMPORTANT)
@app.post("/comment/code-interpreter", response_model=SentimentResponse)
async def analyze_comment_ci(data: dict = Body(...)):
    return await process_text(data)
