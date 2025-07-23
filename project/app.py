import os
import json
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
from openai import OpenAI
from numpy.linalg import norm
import fitz
from flask_cors import CORS


from dotenv import load_dotenv
load_dotenv()
# Initialize OpenAI client


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app) 

IMAGE_FOLDER = "image_knowledge_artifacts"
EMBED_FILE = "embeddings.json"
CHUNK_SIZE = 1000

def load_embeddings():
    if os.path.exists(EMBED_FILE):
        with open(EMBED_FILE, "r") as f:
            return json.load(f)
    return generate_embeddings()

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def generate_embeddings():
    all_data = []
    for file in sorted(os.listdir(IMAGE_FOLDER)):
        path = os.path.join(IMAGE_FOLDER, file)
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            text = pytesseract.image_to_string(Image.open(path))
        elif file.lower().endswith(".pdf"):
            text = extract_text_from_pdf(path)
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

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    if not user_input:
        return jsonify({"reply": "No message provided."})

    top_chunks = retrieve_relevant_chunks(user_input, EMBEDDINGS)
    context = "\n\n".join(top_chunks)

    messages = [
        {"role": "system", "content": "Answer using only the following knowledge:\n" + context},
        {"role": "user", "content": user_input}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    return jsonify({"reply": response.choices[0].message.content})

if __name__ == "__main__":
    print("⏳ Generating embeddings...")
    EMBEDDINGS = load_embeddings()
    print("✅ Ready to chat.")
    app.run(port=5000)
