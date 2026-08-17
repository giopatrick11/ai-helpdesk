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
from pypdf import PdfReader
from io import BytesIO

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.document import Document

from app.schemas.document import (
    DocumentCreate,
    DocumentSearchRequest,
    RagQuestionRequest,
)

from app.services.document_service import create_document
from app.services.retrieval_service import search_documents
from app.services.rag_service import ask_rag
from app.queue.connection import ai_queue
from app.jobs.document_jobs import process_document

router = APIRouter()


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

    ai_queue.enqueue(
        process_document,
        document.id,
    )

    return {
        "id": document.id,
        "title": document.title,
        "status": document.status,
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

    file_bytes = await file.read()

    reader = PdfReader(
        BytesIO(file_bytes)
    )

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    content = "\n\n".join(pages)

    if not content.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in PDF",
        )

    document = create_document(
        db=db,
        user_id=current_user.id,
        title=title,
        filename=file.filename,
        content=content,
    )

    ai_queue.enqueue(
    process_document,
    document.id,
)

    return {
    "id": document.id,
    "title": document.title,
    "filename": document.filename,
    "status": document.status,
    "pages": len(reader.pages),
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