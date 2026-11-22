# AI Document Intelligence 📄🤖

An AI-powered PDF Question Answering System built using Retrieval-Augmented Generation (RAG). Upload PDF documents and ask questions to receive relevant answers with source references from the uploaded document.

## 🚀 Features

- Upload PDF documents
- Extract text from PDF files
- Split text into smaller chunks
- Generate text embeddings
- Store embeddings using ChromaDB
- Perform semantic search
- Ask questions about uploaded documents
- Generate answers using a local LLM
- Display relevant PDF source references
- Interactive React-based chat interface

## 🛠️ Technologies Used

**Frontend**
- React.js
- Vite
- Axios
- CSS

**Backend**
- Python
- FastAPI
- PyPDF

**AI & Machine Learning**
- FastEmbed
- Sentence Transformers (all-MiniLM-L6-v2)
- Ollama (Llama 3.2:3B)
- Retrieval-Augmented Generation (RAG)

**Vector Database**
- ChromaDB

## 🏗️ Project Architecture

1. User uploads a PDF through the React frontend.
2. FastAPI extracts text from the PDF.
3. Extracted text is divided into chunks.
4. FastEmbed generates embeddings for each chunk.
5. ChromaDB stores the embeddings and document metadata.
6. User submits a question.
7. Semantic search retrieves relevant chunks.
8. Ollama generates an answer using the retrieved context.
9. The frontend displays the answer and its source references.

## 📁 Project Structure

```text
AI-Document-Intelligence/
│
├── backend/
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── ...
│
├── documents/
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/aallahbakash13-ctrl/AI-Document-Intelligence.git
cd AI-Document-Intelligence
```

### 2. Create and activate a Python virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

Backend API: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

### 5. Install frontend dependencies

Open another terminal:

```bash
cd frontend
npm install
```

### 6. Start the frontend

```bash
npm run dev
```

Frontend: http://localhost:5173

### 7. Start Ollama

Install Ollama and download the required model:

```bash
ollama pull llama3.2:3b
```

Ensure Ollama is running before asking questions.

## 🎯 Project Objective

The objective of this project is to make document understanding easier by combining semantic search and Large Language Models. It helps users retrieve information from PDF documents without manually searching through every page.

## 📚 Learning Outcomes

- Understanding Retrieval-Augmented Generation (RAG)
- Working with Large Language Models
- Text preprocessing and chunking
- Generating text embeddings
- Vector database integration
- Building REST APIs using FastAPI
- Connecting React frontend with Python backend

## 👨‍💻 Author

AI & Machine Learning Student

**Project:** AI Document Intelligence

---

⭐ If you find this project interesting, feel free to explore the repository!