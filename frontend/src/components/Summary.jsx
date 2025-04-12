import React, { useState } from 'react';

const Summary = () => {
  const [text, setText] = useState('');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSummarize = async () => {
    if (!text.trim()) return alert("Please enter a legal document to summarize.");

    setLoading(true);
    setSummary('');

    try {
        const res = await fetch('http://localhost:8000/api/summarize', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
          });
          
      const data = await res.json();
      setSummary(data.summary || 'No summary returned.');
    } catch (error) {
      console.error("Summarization failed:", error);
      setSummary("❌ Error summarizing the document.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4 text-center">🧾 Legal Document Summarizer</h1>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste your legal document here..."
        rows="10"
        className="w-full p-4 border rounded-md mb-4 resize-none"
      />

      <div className="flex justify-center mb-4">
        <button
          onClick={handleSummarize}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          {loading ? 'Summarizing...' : 'Summarize Document'}
        </button>
      </div>

      {summary && (
        <div className="bg-gray-100 p-4 rounded-md shadow">
          <h2 className="text-xl font-semibold mb-2">📄 Summary:</h2>
          <p className="whitespace-pre-wrap">{summary}</p>
        </div>
      )}
    </div>
  );
};

export default Summary;
