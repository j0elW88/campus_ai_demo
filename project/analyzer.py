import json
import os
from collections import defaultdict
from typing import List, Dict
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File to store parameter suggestions
PARAMETER_FILE = "analyzer_output.txt"
TRUST_THRESHOLD = 3  # Minimum confirmations to make something trusted

# In-memory store for parameter suggestions and their vote counts
parameter_votes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
trusted_parameters: Dict[str, str] = {}


def is_generic_or_personal(messages: List[Dict]) -> bool:
    user_text = "\n".join([m["content"] for m in messages if m["role"] == "user"])

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a filter. Determine if the user's question is too personal, vague, or general to be stored as a reusable parameter. "
                        "Reply with 'yes' if the query is personal (e.g. 'What should I eat today?', 'Who is the best manager?') or general small talk. "
                        "Reply with 'no' if it is a task-specific or organizational question (e.g. 'how to get a routing number')."
                    )
                },
                {
                    "role": "user",
                    "content": f"Should this be filtered out? {user_text}"
                }
            ]
        )
        answer = response.choices[0].message.content.strip().lower()
        return "yes" in answer
    except Exception as e:
        print(f"⚠️ Filter classification failed: {e}")
        return False  # Fail safe to allow intent if GPT is down



def classify_intent_open_ended(messages: List[Dict]) -> str:
    user_text = "\n".join([m["content"] for m in messages if m["role"] == "user"])
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI that infers and names user intent in a short, lowercase snake_case label. "
                        "Avoid using generic labels like 'general_query'. Instead, generate a concise but specific label like "
                        "'compare_interest_rates', 'find_fee_policy', or 'print_check_procedure' based on the actual user goal."
                    )
                },
                {
                    "role": "user",
                    "content": f"What is the user's intent? Here's the conversation:\n\n{user_text}"
                }
            ]
        )
        return response.choices[0].message.content.strip().lower().replace(" ", "_")
    except Exception as e:
        print(f"GPT dynamic intent classification failed: {e}")
        return "unknown_intent"


def load_existing_suggestions():
    if os.path.exists(PARAMETER_FILE):
        with open(PARAMETER_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("#") or not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    key = obj.get("parameter")
                    suggestion = obj.get("value")
                    if obj.get("status") == "trusted":
                        trusted_parameters[key] = suggestion
                    else:
                        parameter_votes[key][suggestion] += 1
                except Exception as e:
                    print(f"⚠️ Error loading suggestion: {e}")


def save_suggestion(parameter: str, value: str, trusted: bool = False):
    data = {
        "parameter": parameter,
        "value": value,
        "status": "trusted" if trusted else "tentative"
    }
    with open(PARAMETER_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")


def suggest_parameter(key: str, new_value: str) -> Dict[str, str]:
    if key in trusted_parameters:
        if trusted_parameters[key] == new_value:
            return {"status": "unchanged", "trusted": True, "parameter": key, "value": new_value}
        else:
            return {
                "status": "conflict",
                "trusted_value": trusted_parameters[key],
                "new_value": new_value,
                "action": "ask_user_to_choose"
            }

    parameter_votes[key][new_value] += 1
    if parameter_votes[key][new_value] >= TRUST_THRESHOLD:
        trusted_parameters[key] = new_value
        save_suggestion(key, new_value, trusted=True)
        return {"status": "promoted", "parameter": key, "value": new_value}
    else:
        save_suggestion(key, new_value, trusted=False)
        return {"status": "pending", "votes": parameter_votes[key][new_value], "needed": TRUST_THRESHOLD}


def analyze_chat(messages: List[Dict], rating: str, optional_feedback: str = None) -> List[Dict]:
    """
    Entry point for feedback-based analyzer.
    Tags feedback, identifies potential user intents and returns pathway suggestions.
    """
    results = []
    try:
        # ✅ Log all questions to question log
        store_question_types(messages)

        # ❌ Skip intent classification if the query is too personal or vague
        if is_generic_or_personal(messages):
            print("🚫 Skipping parameter suggestion: personal or non-reusable input")
        else:
            inferred_intent = classify_intent_open_ended(messages)
            results.append(suggest_parameter("intent", inferred_intent))

    except Exception as e:
        results.append({"error": str(e)})

    return results


# Initial load
load_existing_suggestions()

QUESTION_LOG = "question_types_log.json"

def store_question_types(messages: List[Dict]):
    if not messages:
        return

    user_questions = [m["content"] for m in messages if m["role"] == "user"]
    if not user_questions:
        return

    if os.path.exists(QUESTION_LOG):
        with open(QUESTION_LOG, "r") as f:
            data = json.load(f)
    else:
        data = []

    for q in user_questions:
        data.append({
            "question": q,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        })

    with open(QUESTION_LOG, "w") as f:
        json.dump(data, f, indent=2)

def get_trusted_parameters() -> Dict[str, str]:
    return trusted_parameters