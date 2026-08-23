import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import api from "../api/client";

type Document = {
  id: number;
  title: string;
  filename: string | null;
  status: string;
  created_at: string;
};

type RagSource = {
  chunk_id?: number;
  document_id: number;
  title: string;
  distance?: number;
};

type RagResponse = {
  answer: string;
  sources: RagSource[];
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");
  const [ragResponse, setRagResponse] = useState<RagResponse | null>(null);
  const [deletingDocumentIds, setDeletingDocumentIds] = useState<number[]>([]);
  const [deleteError, setDeleteError] = useState("");

  const loadDocuments = useCallback(async () => {
    try {
      const response = await api.get("/documents/");

      setDocuments(response.data);
      setError("");
    } catch {
      setError("Could not load documents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    const hasProcessingDocument = documents.some(
      (document) => document.status === "processing",
    );

    if (!hasProcessingDocument) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadDocuments();
    }, 2000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [documents, loadDocuments]);

  async function handleUpload(event: FormEvent) {
    event.preventDefault();

    if (!file) {
      setUploadError("Choose a PDF file to upload.");
      setUploadSuccess("");
      return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("file", file);

    setUploading(true);
    setUploadError("");
    setUploadSuccess("");

    try {
      await api.post("/documents/upload-pdf", formData);

      setTitle("");
      setFile(null);
      setFileInputKey((currentKey) => currentKey + 1);
      setUploadSuccess("Document uploaded.");

      await loadDocuments();
    } catch {
      setUploadError("Could not upload document.");
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk(event: FormEvent) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      return;
    }

    setAsking(true);
    setAskError("");

    try {
      const response = await api.post<RagResponse>("/documents/ask", {
        question: trimmedQuestion,
      });

      setRagResponse(response.data);
    } catch {
      setAskError("Could not ask the knowledge base.");
    } finally {
      setAsking(false);
    }
  }

  async function handleDelete(document: Document) {
    const confirmed = window.confirm(
      `Delete "${document.title}"?`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingDocumentIds((currentIds) => [
      ...currentIds,
      document.id,
    ]);
    setDeleteError("");

    try {
      await api.delete(`/documents/${document.id}`);

      setDocuments((currentDocuments) =>
        currentDocuments.filter(
          (currentDocument) => currentDocument.id !== document.id,
        ),
      );
    } catch {
      setDeleteError("Could not delete document.");
    } finally {
      setDeletingDocumentIds((currentIds) =>
        currentIds.filter((documentId) => documentId !== document.id),
      );
    }
  }

  if (loading) {
    return <p>Loading documents...</p>;
  }

  return (
    <div>
      <h1>Documents</h1>

      <form onSubmit={handleUpload}>
        <div>
          <label htmlFor="document-title">Title</label>

          <input
            id="document-title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
          />
        </div>

        <div>
          <label htmlFor="document-file">PDF File</label>

          <input
            key={fileInputKey}
            id="document-file"
            type="file"
            accept="application/pdf"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            required
          />
        </div>

        {uploadError && <p>{uploadError}</p>}
        {uploadSuccess && <p>{uploadSuccess}</p>}

        <button type="submit" disabled={uploading}>
          {uploading ? "Uploading..." : "Upload PDF"}
        </button>
      </form>

      <hr />

      <section>
        <h2>Ask Knowledge Base</h2>

        <form onSubmit={handleAsk}>
          <div>
            <label htmlFor="knowledge-question">Question</label>

            <textarea
              id="knowledge-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              required
            />
          </div>

          {askError && <p>{askError}</p>}

          <button type="submit" disabled={asking || !question.trim()}>
            {asking ? "Asking..." : "Ask"}
          </button>
        </form>

        {ragResponse && (
          <div>
            <h3>Answer</h3>
            <p>{ragResponse.answer}</p>

            <h3>Sources</h3>

            {ragResponse.sources.length === 0 ? (
              <p>No sources returned.</p>
            ) : (
              ragResponse.sources.map((source) => (
                <div key={`${source.document_id}-${source.chunk_id ?? "source"}`}>
                  <p>Title: {source.title}</p>
                  <p>Document ID: {source.document_id}</p>
                  {source.distance !== undefined && (
                    <p>Distance: {source.distance}</p>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </section>

      <hr />

      {error && <p>{error}</p>}
      {deleteError && <p>{deleteError}</p>}

      {!error && documents.length === 0 ? (
        <p>No documents yet.</p>
      ) : (
        documents.map((document) => {
          const isDeleting = deletingDocumentIds.includes(document.id);

          return (
            <div key={document.id}>
              <h2>{document.title}</h2>

              <p>ID: {document.id}</p>
              <p>Filename: {document.filename ?? "None"}</p>
              <p>Status: {document.status}</p>
              <p>Created: {document.created_at}</p>

              <button
                type="button"
                disabled={isDeleting}
                onClick={() => {
                  void handleDelete(document);
                }}
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </button>

              <hr />
            </div>
          );
        })
      )}
    </div>
  );
}
