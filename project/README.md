# Empower AI – Internal Assistant

Empower AI is an internal-facing assistant designed to help employees access accurate information from approved knowledge artifacts. The system retrieves and summarizes internal documentation using embedding-based search and either OpenAI or local LLMs.

## Features

- Processes and embeds knowledge artifacts (PDFs and images)
- Retrieves relevant document content based on user questions
- Supports OpenAI (GPT-3.5) or local models (e.g. LLaMA 3.2)
- Enforces a master system prompt for consistent and policy-compliant responses
- Offers a simple API endpoint for front-end integration

---

## Project Structure

```
project/
├── app.py                    # Main Flask app
├── .env                      # Environment variables
├── requiredPrompting.txt     # System-level behavior prompt
├── embeddings.json           # Cached embeddings file (auto-generated)
├── image_knowledge_artifacts/ # Folder of PDF/image-based KB sources
└── client/                   # Optional React frontend
```

---

## Setup Instructions

### 1. Environment Setup

Install Python packages:

```bash
pip install -r requirements.txt
```

Required packages include:

- Flask
- flask-cors
- openai
- pytesseract
- numpy
- PyMuPDF
- python-dotenv
- requests

Tesseract must also be installed and available in your system PATH.

### 2. Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_key
USE_OTHER=false
OTHER_MODEL=llama3.2:1b
```

Set `USE_OTHER=true` if using a local Ollama model.

---

### 3. Add Knowledge Files

Add internal documentation (PDF, PNG, JPG, etc.) to:

```
/image_knowledge_artifacts
```

Text will be extracted using OCR or PDF parsing and embedded for semantic search.

---

### 4. Define System Prompt

Add a `requiredPrompting.txt` file with your system behavior rules. This file defines how the assistant should interpret, prioritize, and respond to queries. It will always be used as the system prompt at runtime.

---

### 5. Start the Application

Run the backend:

```bash
python app.py
```

The first run will generate `embeddings.json` based on the documents in `image_knowledge_artifacts`.

The app will be available at:

```
http://localhost:5000/chat
```

Send a POST request with:

```json
{ "message": "Your question here" }
```

---

## Ollama Integration (Optional)

To use a local LLM model instead of OpenAI:

1. Install Ollama: https://ollama.com
2. Download and run a model:

```bash
ollama run llama3.2:1b
```

3. Update your `.env` file:

```env
USE_OTHER=true
OTHER_MODEL=llama3.2:1b
```

Restart the backend. All responses will be routed through the local model.

---

## Response Behavior Overview

- Never hallucinate or guess when documents are not clear
- Always follow knowledge article instructions, especially when something is stated as "not allowed" or "should not"
- When no relevant information exists, respond with:

> "This is not explicitly stated in the knowledge article. Please consult a supervisor for confirmation."

---

## Notes

- Embeddings are stored in `embeddings.json` and are regenerated only when missing.
- System prompt logic is enforced for every user query.
- For frontend integration, use the `/chat` endpoint and connect via simple POST requests.