from pydantic import BaseModel


class DocumentCreate(BaseModel):
    title: str
    content: str

class DocumentSearchRequest(BaseModel):
    question: str

class RagQuestionRequest(BaseModel):
    question: str