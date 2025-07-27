import React, { useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [uploaded, setUploaded] = useState(false);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a resume file first");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/upload_resume/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploaded(true);
      alert(res.data.message);
    } catch (error) {
      alert("Upload failed: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!query) {
      alert("Enter a question");
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/chat/`, { query });
      setSuggestions(res.data.suggestions || []);
    } catch (error) {
      alert("Chat failed: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Function to split heading and description
  const splitHeading = (text) => {
    const parts = text.split(":");
    if (parts.length > 1) {
      return {
        heading: parts[0].replace(/\*/g, "").trim(),
        description: parts.slice(1).join(":").trim(),
      };
    }
    return { heading: "", description: text };
  };

  return (
    <div className="app-container">
      <h1 className="title">AI Career Guide (Gemini 2.0)</h1>

      <div className="upload-section">
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button className="btn" onClick={handleUpload} disabled={loading}>
          {loading ? "Uploading..." : "Upload Resume"}
        </button>
      </div>

      {uploaded && (
        <div className="query-section">
          <textarea
            rows="3"
            placeholder="Ask a question about your resume..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn" onClick={handleChat} disabled={loading}>
            {loading ? "Thinking..." : "Ask AI"}
          </button>
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="suggestion-container">
          <h3>AI Suggestions</h3>
          <div className="card-grid">
            {suggestions.map((point, idx) => {
              const { heading, description } = splitHeading(point);
              return (
                <div key={idx} className="card">
                  <span className="badge">{idx + 1}</span>
                  {heading && <h4>{heading}</h4>}
                  <p>{description}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
