from fastapi.middleware.cors import CORSMiddleware
import ollama
from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
from uuid import uuid4, UUID
from pypdf import PdfReader
from fastembed import TextEmbedding
import chromadb

app = FastAPI(title="AI Document Intelligence")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embedding model
embedding_model = TextEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Document storage folder
BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENT_DIR = BASE_DIR / "documents"
DOCUMENT_DIR.mkdir(exist_ok=True)

# ChromaDB persistent storage
CHROMA_DIR = BASE_DIR / "chroma_db"

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="pdf_documents"
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "AI Document Intelligence API is running!"
    }


# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# PDF upload

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    # 1. Validate PDF file
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size must not exceed 10 MB"
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file"
        )

    document_id = str(uuid4())
    file_path = DOCUMENT_DIR / f"{document_id}.pdf"

    try:
        # 2. Save PDF
        file_path.write_bytes(content)

        # 3. Extract PDF text
        reader = PdfReader(str(file_path))

        extracted_text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in PDF"
            )

        # 4. Split text into chunks
        chunks = split_text_into_chunks(extracted_text)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Unable to create text chunks"
            )

        # 5. Generate embeddings
        embeddings = [
            embedding.tolist()
            for embedding in embedding_model.embed(chunks)
        ]

        # 6. Store in ChromaDB
        chunk_ids = [
            f"{document_id}_chunk_{i}"
            for i in range(len(chunks))
        ]

        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]

        collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        await file.close()

        return {
            "message": "PDF uploaded and processed successfully!",
            "document_id": document_id,
            "filename": file.filename,
            "size_bytes": len(content),
            "total_chunks": len(chunks),
            "embedding_dimensions": len(embeddings[0]),
            "stored_in": "ChromaDB"
        }

    except HTTPException:
        await file.close()
        raise

    except Exception as e:
        await file.close()

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )

# Extract text from PDF
@app.get("/extract-text/{document_id}")
def extract_text(document_id: str):

    try:
        valid_id = str(UUID(document_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID"
        )

    file_path = DOCUMENT_DIR / f"{valid_id}.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    try:
        reader = PdfReader(str(file_path))
        extracted_text = ""

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            extracted_text += (
                f"\n--- Page {page_number} ---\n"
                + page_text
            )

        return {
            "message": "Text extracted successfully!",
            "total_pages": len(reader.pages),
            "extracted_text": extracted_text
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read this PDF"
        )


# Split text into chunks

import re

def split_text_into_chunks(text: str):
    # Find question markers such as Q1., Q2., Q10.
    parts = re.split(r'(?=Q\s*\d+\s*\.)', text, flags=re.IGNORECASE)

    chunks = []

    for part in parts:
        part = part.strip()

        if part:
            chunks.append(part)

    return chunks


# Chunk PDF text
@app.get("/chunk-text/{document_id}")
def chunk_text(document_id: str):

    try:
        valid_id = str(UUID(document_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID"
        )

    file_path = DOCUMENT_DIR / f"{valid_id}.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    try:
        reader = PdfReader(str(file_path))

        extracted_text = ""

        for page in reader.pages:
            extracted_text += (page.extract_text() or "") + "\n"

        chunks = split_text_into_chunks(extracted_text)

        return {
            "message": "Text chunking successful!",
            "total_chunks": len(chunks),
            "chunks": chunks
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to process this PDF"
        )


# Generate embeddings
def generate_embeddings(chunks):

    embeddings = list(embedding_model.embed(chunks))

    return [
        embedding.tolist()
        for embedding in embeddings
    ]


# Generate and store embeddings in ChromaDB
@app.get("/generate-embeddings/{document_id}")
def create_embeddings(document_id: str):

    try:
        valid_id = str(UUID(document_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID"
        )

    file_path = DOCUMENT_DIR / f"{valid_id}.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    try:
        reader = PdfReader(str(file_path))

        extracted_text = ""

        for page in reader.pages:
            extracted_text += (page.extract_text() or "") + "\n"

        chunks = split_text_into_chunks(extracted_text)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text found in this PDF"
            )

        embeddings = generate_embeddings(chunks)

        chunk_ids = [
            f"{valid_id}_chunk_{i}"
            for i in range(len(chunks))
        ]

        collection.upsert(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=[
                {
                    "document_id": valid_id,
                    "chunk_number": i
                }
                for i in range(len(chunks))
            ]
        )

        return {
            "message": "Embeddings generated and stored successfully!",
            "document_id": valid_id,
            "total_chunks": len(chunks),
            "embedding_dimensions": len(embeddings[0]),
            "stored_in": "ChromaDB"
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate or store embeddings"
        )

@app.get("/search/{document_id}")
def search_document(document_id: str, query: str):

    # Validate document ID
    try:
        valid_id = str(UUID(document_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID"
        )

    # Check whether document exists
    file_path = DOCUMENT_DIR / f"{valid_id}.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )

    # Generate embedding for the user's question
    query_embedding = generate_embeddings([query])[0]

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where={"document_id": valid_id}
    )

    return {
        "message": "Similarity search successful!",
        "query": query,
        "results": results["documents"][0] if results["documents"] else []
    }
from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str



@app.post("/ask/{document_id}")
def ask_document(document_id: str, request: QuestionRequest):

    # Validate document ID
    try:
        valid_id = str(UUID(document_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID"
        )

    # Check whether PDF exists
    file_path = DOCUMENT_DIR / f"{valid_id}.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    # Generate question embedding
    query_embedding = generate_embeddings([question])[0]

    # Retrieve relevant chunks from ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=4,
        where={"document_id": valid_id}
    )

    retrieved_chunks = (
        results["documents"][0]
        if results["documents"]
        else []
    )

    if not retrieved_chunks:
        raise HTTPException(
            status_code=404,
            detail="No document content found."
        )

    # Prepare numbered source references
    sources = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        sources.append({
            "source_id": index,
            "content": chunk
        })

    # Prepare document context
    context = "\n\n".join(
        f"[Source {source['source_id']}]\n{source['content']}"
        for source in sources
    )

    # Generate answer using Ollama
    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI document assistant. "
                    "Answer using only the supplied document context. "
                    "Include source references such as [Source 1] "
                    "when supporting your answer. "
                    "If information is unavailable, say so. "
                    "Never invent facts."
                )
            },
            {
                "role": "user",
                "content": f"""
Document Context:
{context}

Question:
{question}
"""
            }
        ]
    )

    answer = response["message"]["content"]

    return {
        "message": "Answer generated successfully!",
        "document_id": valid_id,
        "question": question,
        "answer": answer,
        "sources": sources
    }
