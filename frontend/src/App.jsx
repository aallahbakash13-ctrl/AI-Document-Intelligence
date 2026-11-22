

import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState("");
  const [message, setMessage] = useState("");
  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);

  const uploadPDF = async () => {
    if (!file) {
      setMessage("Please select a PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploading(true);
      setMessage("Uploading and processing PDF...");

      const response = await axios.post(
        "http://127.0.0.1:8000/upload-pdf",
        formData
      );

      setDocumentId(response.data.document_id);
      setMessage("PDF uploaded and processed successfully!");
      setChatHistory([]);
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "PDF upload failed."
      );
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim() || !documentId || asking) return;

    const currentQuestion = question.trim();

    setChatHistory((previous) => [
      ...previous,
      {
        type: "question",
        text: currentQuestion
      }
    ]);

    setQuestion("");
    setAsking(true);

    try {
      const response = await axios.post(
        `http://127.0.0.1:8000/ask/${documentId}`,
        { question: currentQuestion }
      );

      setChatHistory((previous) => [
        ...previous,
        {
          type: "answer",
          text: response.data.answer,
          sources: response.data.sources || []
        }
      ]);
    } catch (error) {
      setChatHistory((previous) => [
        ...previous,
        {
          type: "answer",
          text:
            error.response?.data?.detail ||
            "Unable to generate an answer. Please try again."
        }
      ]);
      console.error(error);
    } finally {
      setAsking(false);
    }
  };

  const clearChat = () => {
    setChatHistory([]);
  };

  return (
    <div className="App">
      <h1>AI Document Intelligence</h1>
      <p>Your smart AI-powered PDF assistant</p>

      <div className="upload-card">
        <div className="upload-icon">📄</div>

        <h2>Upload Your Document</h2>
        <p>Select a PDF and let AI understand your document.</p>

        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <button onClick={uploadPDF} disabled={uploading}>
          {uploading ? "Processing..." : "🚀 Upload PDF"}
        </button>

        <div className="status">{message}</div>

        {documentId && (
          <>
            <div className="document-id">
              Document ID: {documentId}
            </div>

            <div className="question-section">
              <h2>🤖 Ask Your Document</h2>
              <p>Ask questions and get answers from your PDF.</p>

              <div className="chat-history">
                {chatHistory.map((chat, index) => (
                  <div
                    key={index}
                    className={`chat-message ${chat.type}`}
                  >
                    <strong>
                      {chat.type === "question"
                        ? "You"
                        : "AI Assistant"}
                    </strong>

                    <p>{chat.text}</p>

                    {chat.sources && chat.sources.length > 0 && (
                      <div className="sources-section">
                        <h4>📚 PDF Sources</h4>

                        {chat.sources.map((source) => (
                          <div
                            className="source-card"
                            key={source.source_id}
                          >
                            <strong>
                              Source {source.source_id}
                            </strong>
                            <p>{source.content}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {asking && (
                  <div className="chat-message answer">
                    <strong>AI Assistant</strong>
                    <p>Thinking...</p>
                  </div>
                )}
              </div>

              <textarea
                placeholder="Ask something about your PDF..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    askQuestion();
                  }
                }}
              />

              <button onClick={askQuestion} disabled={asking}>
                {asking ? "Thinking..." : "✨ Ask AI"}
              </button>

              <button
                className="clear-button"
                onClick={clearChat}
                disabled={chatHistory.length === 0 || asking}
              >
                🗑 Clear Chat
              </button>
            </div>
          </>
        )}
      </div>

      <div className="footer">
        Powered by React • FastAPI • ChromaDB • Ollama
      </div>
    </div>
  );
}

export default App;
