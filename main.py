from fastapi import FastAPI, Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AIPIPE_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDI5ODdAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.0ByYJrCcZMkknLE0YWztzn37XUbr3Q5OKu_4P_EM4jQ"


class SentimentResponse(BaseModel):
    sentiment: str
    rating: int


# 🔥 Safe fallback (never crashes)
def fallback_response():
    return {"sentiment": "neutral", "rating": 3}


async def process_text(data: dict):
    try:
        text = data.get("comment") or data.get("code")

        if not text:
            return fallback_response()

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
            return fallback_response()

        response_json = r.json()

        output_text = None
        if "output" in response_json:
            for item in response_json["output"]:
                if "content" in item:
                    for c in item["content"]:
                        if c.get("type") == "output_text":
                            output_text = c.get("text")

        if not output_text:
            return fallback_response()

        return json.loads(output_text)

    except:
        return fallback_response()


@app.post("/comment", response_model=SentimentResponse)
async def analyze_comment(data: dict = Body(...)):
    return await process_text(data)


@app.post("/comment/code-interpreter", response_model=SentimentResponse)
async def analyze_comment_ci(data: dict = Body(...)):
    return await process_text(data)
