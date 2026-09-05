from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
    Response,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.document import Document

from app.schemas.document import (
    DocumentCreate,
    DocumentSearchRequest,
    RagQuestionRequest,
)

from app.config import MAX_PDF_UPLOAD_BYTES
from app.services.document_service import (
    PDFProcessingError,
    create_document,
    extract_pdf_text,
)
from app.services.retrieval_service import search_documents
from app.services.rag_service import ask_rag
from app.queue.connection import AI_JOB_RETRY, ai_queue
from app.jobs.document_jobs import process_document

router = APIRouter()


def enqueue_document_processing(document: Document, db: Session) -> None:
    try:
        ai_queue.enqueue(
            process_document,
            document.id,
            retry=AI_JOB_RETRY,
        )
    except Exception:
        document.status = "failed"
        document.processing_error = "Document processing could not be queued."
        db.commit()
        db.refresh(document)


@router.post("/", status_code=201)
def upload_document(
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = create_document(
        db=db,
        user_id=current_user.id,
        title=document_data.title,
        content=document_data.content,
    )

    enqueue_document_processing(document, db)

    return {
        "id": document.id,
        "title": document.title,
        "status": document.status,
        "processing_error": document.processing_error,
    }


@router.post("/search")
def search_document_chunks(
    search_data: DocumentSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = search_documents(
        db=db,
        user_id=current_user.id,
        question=search_data.question,
    )

    return [
        {
            "id": result["chunk"].id,
            "document_id": result["document"].id,
            "title": result["document"].title,
            "content": result["chunk"].content,
            "distance": result["distance"],
        }
        for result in results
    ]


@router.post("/ask")
def ask_document_question(
    request: RagQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ask_rag(
        db=db,
        user_id=current_user.id,
        question=request.question,
    )


@router.post("/upload-pdf", status_code=201)
async def upload_pdf(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed",
        )

    file_bytes = await file.read(MAX_PDF_UPLOAD_BYTES + 1)

    if len(file_bytes) > MAX_PDF_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="PDF file is too large",
        )

    try:
        content, page_count = extract_pdf_text(file_bytes)
    except PDFProcessingError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    document = create_document(
        db=db,
        user_id=current_user.id,
        title=title,
        filename=file.filename,
        content=content,
    )

    enqueue_document_processing(document, db)

    return {
        "id": document.id,
        "title": document.title,
        "filename": document.filename,
        "status": document.status,
        "processing_error": document.processing_error,
        "pages": page_count,
    }


@router.get("/")
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).all()

    return [
        {
            "id": document.id,
            "title": document.title,
            "filename": document.filename,
            "status": document.status,
            "processing_error": document.processing_error,
            "created_at": document.created_at,
        }
        for document in documents
    ]


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    chunk_count = len(document.chunks)

    return {
        "id": document.id,
        "title": document.title,
        "filename": document.filename,
        "status": document.status,
        "processing_error": document.processing_error,
        "chunk_count": chunk_count,
        "created_at": document.created_at,
    }


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    db.delete(document)
    db.commit()

    return Response(status_code=204)
