# self_review.py
import os
import json
from datetime import datetime
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from .analyzer import analyze_conversation

load_dotenv()

router = APIRouter()

ENABLE_SELF_REVIEW = os.getenv("ENABLE_SELF_REVIEW", "false").lower() == "true"
HISTORY_PATH = "reviews/history.jsonl"

class Message(BaseModel):
    role: str
    content: str

class ReviewRequest(BaseModel):
    rating: str  # 'good' or 'bad'
    messages: List[Message]
    feedback: Optional[str] = None

@router.post("/review")
async def review_conversation(req: ReviewRequest):
    if not ENABLE_SELF_REVIEW:
        return {"status": "skipped", "reason": "self-review disabled"}

    summary_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "rating": req.rating,
        "feedback": req.feedback or None,
        "messages": [msg.dict() for msg in req.messages],
    }

    # Analyze conversation and generate parameterization
    summary_data["pathways"] = analyze_conversation(req.messages, req.feedback)

    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary_data) + "\n")

    return {"status": "success", "pathways": summary_data["pathways"]}
