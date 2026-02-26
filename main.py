from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ HARDCODED AI PIPE TOKEN (as you requested)
AIPIPE_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDI5ODdAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.0ByYJrCcZMkknLE0YWztzn37XUbr3Q5OKu_4P_EM4jQ"


# ---------- Request Model ----------
class CommentRequest(BaseModel):
    comment: str = Field(..., min_length=1)


# ---------- Response Model ----------
class SentimentResponse(BaseModel):
    sentiment: str
    rating: int


@app.post("/comment", response_model=SentimentResponse)
async def analyze_comment(data: CommentRequest):
    try:
        url = "https://aipipe.org/openrouter/v1/responses"

        payload = {
            "model": "openai/gpt-4.1-mini",
            "input": f"""
Analyze the sentiment of this comment and return ONLY valid JSON.

Comment: {data.comment}

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

        # 🔎 Safely extract model output text
        output_text = None

        if "output" in response_json:
            for item in response_json["output"]:
                if "content" in item:
                    for c in item["content"]:
                        if c.get("type") == "output_text":
                            output_text = c.get("text")

        if not output_text:
            raise HTTPException(status_code=500, detail="No text output from model")

        # 🔎 Parse JSON safely
        try:
            result = json.loads(output_text)
        except:
            raise HTTPException(status_code=500, detail=f"Invalid JSON returned: {output_text}")

        return result

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))

@app.post("/comment/code-interpreter", response_model=SentimentResponse)
async def analyze_comment_ci(data: CommentRequest):
    return await analyze_comment(data)

