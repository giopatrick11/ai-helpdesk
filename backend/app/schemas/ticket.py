from enum import Enum
from pydantic import BaseModel


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Status(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"


class TicketCreate(BaseModel):
    subject: str
    description: str
    priority: Priority


class TicketUpdate(BaseModel):
    subject: str
    description: str
    priority: Priority
    status: Status