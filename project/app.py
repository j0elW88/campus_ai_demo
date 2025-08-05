import os
import json
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
from pytesseract import Output
from openai import OpenAI
import pdfplumber
from numpy.linalg import norm
import requests
from flask_cors import CORS
import threading
from analyzer import analyze_chat, get_trusted_parameters  #Custom python analyzer for feedback-based learning



api_key = os.getenv("OPENAI_API_KEY")

# Initialize Non-OpenAI Client (For future Ollama or Huggingface Model [Huggingface is not fully supported yet])
USE_OTHER = os.getenv("USE_OTHER", "false").lower() == "true"

# Initialize OpenAI client [Good for bug testing]
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app) 

IMAGE_FOLDER = "image_knowledge_artifacts"
EMBED_FILE = "embeddings.json"
CHUNK_SIZE = 1000


def extract_text_from_image_with_layout(image_path):
    from pytesseract import image_to_data, Output
    from PIL import Image

    img = Image.open(image_path)
    data = image_to_data(img, output_type=Output.DICT)

    lines = {}
    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        if not word or int(data["conf"][i]) < 60:
            continue

        block_num = data["block_num"][i]
        par_num = data["par_num"][i]
        line_num = data["line_num"][i]
        left = data["left"][i]

        # Unique key per visual line (could also add block_num to preserve more structure)
        key = (block_num, par_num, line_num)
        lines.setdefault(key, []).append((left, word))

    # Sort words within lines by horizontal position, and lines by their block/para/line order
    sorted_lines = []
    for key in sorted(lines.keys()):
        words = sorted(lines[key], key=lambda x: x[0])
        line_text = ""
        prev_x = None
        for x, word in words:
            if prev_x is not None and (x - prev_x) > 40:  # spacing threshold (adjustable)
                line_text += "    "  # simulate tabbed spacing
            elif line_text:
                line_text += " "
            line_text += word
            prev_x = x
        last_left = 0
        for left, word in words:
            spacing = "\t" if left - last_left > 60 else " "
            line_text += spacing + word if line_text else word
            last_left = left

        sorted_lines.append(line_text)

    return "\n".join(sorted_lines)


def extract_text_from_image_with_columns(image_path):
    from pytesseract import image_to_data, Output
    from PIL import Image

    img = Image.open(image_path)
    data = image_to_data(img, output_type=Output.DICT)

    lines_by_y = {}
    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        if not word or int(data["conf"][i]) < 60:
            continue

        # Round y to group lines
        y_center = data["top"][i] + data["height"][i] // 2
        rounded_y = round(y_center / 10) * 10  # adjust binning granularity if needed
        lines_by_y.setdefault(rounded_y, []).append({
            "x": data["left"][i],
            "text": word
        })

    # Now sort each line by x to preserve column structure
    structured_lines = []
    for y in sorted(lines_by_y.keys()):
        line = sorted(lines_by_y[y], key=lambda w: w["x"])
        line_text = []
        prev_x = None
        for word in line:
            if prev_x is not None and (word["x"] - prev_x) > 50:  # adjustable threshold
                line_text.append("    ")  # simulate tab separation
            line_text.append(word["text"])
            prev_x = word["x"]
        structured_lines.append(" ".join(line_text))

    return "\n".join(structured_lines)


def load_embeddings():
    if os.path.exists(EMBED_FILE):
        with open(EMBED_FILE, "r") as f:
            return json.load(f)
    return generate_embeddings()

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if not page_text or not page_text.strip():
                # OCR fallback using image of page
                img = page.to_image(resolution=300).original
                page_text = pytesseract.image_to_string(img)
            text += page_text + "\n"
    return text

def generate_embeddings():
    all_data = []
    for file in sorted(os.listdir(IMAGE_FOLDER)):
        path = os.path.join(IMAGE_FOLDER, file)
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            if "grid" in file.lower() or "table" in file.lower():
                text = extract_text_from_image_with_columns(path)
            else:
                text = extract_text_from_image_with_layout(path)
        elif file.lower().endswith(".pdf"):
            text = extract_text_from_pdf(path)
        elif file.lower().endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            continue  # Skip unsupported file types

        # Split into chunks
        chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        for chunk in chunks:
            if chunk.strip():
                res = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=chunk
                )
                all_data.append({
                    "source": file,
                    "text": chunk,
                    "embedding": res.data[0].embedding
                })

    with open(EMBED_FILE, "w") as f:
        json.dump(all_data, f)
    return all_data

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (norm(a) * norm(b))

def retrieve_relevant_chunks(question, embeddings, top_k=3):
    q_embed = client.embeddings.create(
        model="text-embedding-ada-002",
        input=question
    ).data[0].embedding

    scored = [
        (cosine_similarity(q_embed, item["embedding"]), item)
        for item in embeddings
    ]
    top = sorted(scored, reverse=True)[:top_k]
    return [item["text"] for _, item in top]


def load_system_prompt():
    with open("requiredPrompting.txt", "r", encoding="utf-8") as f:
        return f.read()



@app.route("/chat", methods=["POST"])
def chat():
    message_history = request.json.get("messages", [])
    if not message_history:
        return jsonify({"reply": "No messages provided."})

    user_input = message_history[-1]["content"]
    top_chunks = retrieve_relevant_chunks(user_input, EMBEDDINGS)
    context = "\n\n".join(top_chunks)


    # Prepare message history with system prompt and knowledge
    system_prompt = load_system_prompt()


    # Load trusted parameters (e.g. intent: 'check_balance')
    trusted = get_trusted_parameters()
    intent = trusted.get("intent", "general_query")

    
    # Adjust system prompt based on inferred intent
    if intent == "check_balance":
        system_prompt += "\n\nThe user likely wants to check an account balance. Respond clearly and directly."
    elif intent == "review_transactions":
        system_prompt += "\n\nThe user is reviewing recent transactions. Provide accurate chronological information."
    elif intent == "find_routing_number":
        system_prompt += "\n\nThe user is looking for a routing number. Provide the exact number quickly."
    elif intent == "general_query":
        system_prompt += "\n\nThis is a general user query. Use broad helpfulness and clarity."

    
    messages = [{"role": "system", "content": system_prompt + "\n\nUse the following knowledge artifacts when relevant:\n" + context}] + message_history

    if USE_OTHER:
        # Use Local LLM
        model = os.getenv("OTHER_MODEL", "MODEL_NAME")  #configured in .env
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        response = requests.post("http://localhost:11434/api/chat", json=payload, stream=True)

        if response.status_code == 200:
            full_reply = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    if "message" in chunk:
                        full_reply += chunk["message"]["content"]
            return jsonify({"reply": full_reply})
        else:
            print("Ollama error:", response.status_code, response.text)
            return jsonify({"reply": "Error calling Ollama API."}), 500
    else:
        # Default to OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return jsonify({"reply": response.choices[0].message.content})


# Analyzer 
@app.route("/review", methods=["POST"])
def review():
    data = request.get_json()
    rating = data.get("rating")
    messages = data.get("messages", [])
    feedback = data.get("feedback", "")  # optional feedback from user

    # Run analysis in a background thread
    threading.Thread(target=analyze_chat, args=(rating, messages, feedback)).start()

    return jsonify({"status": "review submitted"}), 200


try:
    print("⏳ Generating embeddings...")
    EMBEDDINGS = load_embeddings()
    print("✅ Ready to chat.")
except Exception as e:
    print("❌ Error generating embeddings:", e)
    EMBEDDINGS = []

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)