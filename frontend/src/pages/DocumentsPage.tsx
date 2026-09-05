import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import api from "../api/client";
import AppLayout from "../components/AppLayout";
import { Icon, PageHeader, StatusBadge } from "../components/ui";
import { formatTimestamp } from "../utils/format";

type Document = {
  id: number;
  title: string;
  filename: string | null;
  status: string;
  processing_error: string | null;
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
    let isActive = true;

    api.get<Document[]>("/documents/")
      .then((response) => {
        if (isActive) {
          setDocuments(response.data);
          setError("");
        }
      })
      .catch(() => {
        if (isActive) {
          setError("Could not load documents.");
        }
      })
      .finally(() => {
        if (isActive) {
          setLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

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
    return (
      <AppLayout>
        <p className="message message-loading">Loading documents...</p>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <PageHeader
        eyebrow="AI knowledge workspace"
        title="Knowledge Base"
        description="Manage trusted support content and ask questions grounded in your documents."
      >
        <span className="header-count">
          <Icon name="document" size={16} />
          {documents.length} {documents.length === 1 ? "document" : "documents"}
        </span>
      </PageHeader>

      <div className="knowledge-tools-grid">
        <section className="panel upload-panel">
          <div className="panel-heading">
            <span className="panel-icon"><Icon name="upload" /></span>
            <div>
              <h3>Upload knowledge</h3>
              <p>Add a text-based PDF to make it searchable.</p>
            </div>
          </div>

          <form className="form-stack" onSubmit={handleUpload}>
            <div className="field">
              <label htmlFor="document-title">Document title</label>
              <input
                id="document-title"
                placeholder="e.g. Returns and refunds policy"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="document-file">PDF file</label>
              <div className="upload-dropzone">
                <span className="upload-dropzone-icon"><Icon name="upload" size={22} /></span>
                <div>
                  <strong>{file ? file.name : "Choose a PDF to upload"}</strong>
                  <small>PDF files with selectable text work best</small>
                </div>
                <input
                  key={fileInputKey}
                  id="document-file"
                  type="file"
                  accept="application/pdf"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  required
                />
              </div>
            </div>

            <div className="form-feedback" aria-live="polite">
              {uploadError && <p className="message message-error" role="alert">{uploadError}</p>}
              {uploadSuccess && <p className="message message-success">{uploadSuccess}</p>}
            </div>

            <button className="button button-primary" type="submit" disabled={uploading}>
              {!uploading && <Icon name="upload" size={17} />}
              {uploading ? "Uploading..." : "Upload PDF"}
            </button>
          </form>
        </section>

        <section className="panel assistant-panel">
          <div className="panel-heading">
            <span className="panel-icon panel-icon-ai"><Icon name="sparkles" /></span>
            <div>
              <h3>Ask AI</h3>
              <p>Get answers grounded in ready documents.</p>
            </div>
          </div>

          <form className="form-stack" onSubmit={handleAsk}>
            <div className="field">
              <label htmlFor="knowledge-question">Question</label>
              <textarea
                id="knowledge-question"
                placeholder="Ask about a policy, process, or product..."
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                required
              />
            </div>

            {askError && <p className="message message-error" role="alert">{askError}</p>}

            <button
              className="button button-primary"
              type="submit"
              disabled={asking || !question.trim()}
            >
              {!asking && <Icon name="send" size={17} />}
              {asking ? "Asking..." : "Ask"}
            </button>
          </form>

          {ragResponse && (
            <div className="answer-panel" aria-live="polite">
              <div className="answer-heading">
                <span><Icon name="sparkles" size={17} /></span>
                <h4>Answer</h4>
              </div>
              <p className="answer-copy">{ragResponse.answer}</p>

              <div className="sources-heading">
                <h4>Sources</h4>
                <span>{ragResponse.sources.length}</span>
              </div>

              {ragResponse.sources.length === 0 ? (
                <p className="source-empty">No sources returned.</p>
              ) : (
                <div className="source-list">
                  {ragResponse.sources.map((source) => (
                    <div
                      className="source-card"
                      key={`${source.document_id}-${source.chunk_id ?? "source"}`}
                    >
                      <span className="source-icon"><Icon name="document" size={16} /></span>
                      <div>
                        <strong>{source.title}</strong>
                        <p>Document #{source.document_id}</p>
                      </div>
                      {source.distance !== undefined && (
                        <small>Distance {source.distance.toFixed(3)}</small>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </div>

      <div className="page-messages" aria-live="polite">
        {error && <p className="message message-error" role="alert">{error}</p>}
        {deleteError && <p className="message message-error" role="alert">{deleteError}</p>}
      </div>

      {!error && documents.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon"><Icon name="document" size={22} /></span>
          <h3>No knowledge added yet</h3>
          <p>Upload your first PDF to start building the knowledge base.</p>
        </div>
      ) : (
        <section className="documents-section" aria-labelledby="documents-list-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Content library</p>
              <h3 id="documents-list-title">Documents</h3>
            </div>
            <span className="section-count">{documents.length} total</span>
          </div>

          <div className="document-list">
            {documents.map((document) => {
              const isDeleting = deletingDocumentIds.includes(document.id);

              return (
                <article className="document-card" key={document.id}>
                  <span className="document-card-icon"><Icon name="document" size={20} /></span>
                  <div className="document-card-main">
                    <div className="document-card-title">
                      <p className="document-id">Document #{document.id}</p>
                      <h3>{document.title}</h3>
                    </div>
                    <div className="document-meta">
                      <span>{document.filename ?? "No filename"}</span>
                      <span aria-hidden="true">•</span>
                      <span>{formatTimestamp(document.created_at)}</span>
                    </div>
                    {document.status === "failed" && (
                      <p className="message message-error" role="alert">
                        {document.processing_error ?? "Document processing failed."}
                      </p>
                    )}
                  </div>
                  <StatusBadge value={document.status} />
                  <button
                    className="icon-button danger-icon-button"
                    type="button"
                    disabled={isDeleting}
                    aria-label={`Delete ${document.title}`}
                    onClick={() => {
                      void handleDelete(document);
                    }}
                  >
                    <Icon name="trash" size={17} />
                    <span className="desktop-delete-label">
                      {isDeleting ? "Deleting..." : "Delete"}
                    </span>
                  </button>
                </article>
              );
            })}
          </div>
        </section>
      )}
    </AppLayout>
  );
}
