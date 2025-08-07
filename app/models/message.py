from sqlalchemy import (
    Column, Text, Enum, ForeignKey, TIMESTAMP, func, String, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, mapped_column
import enum
import uuid
from app.models.base_model import Base 
from sqlalchemy.orm import relationship


class MessageRole(enum.Enum):
    USER = "USER"
    AI = "AI"
    SYSTEM = "SYSTEM"
    TOOL = "TOOL"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = mapped_column(String(50), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = mapped_column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role = mapped_column(Enum(MessageRole, name="message_role"), nullable=False)
    content = mapped_column(Text, nullable=False)
    created_at = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())


    def __init__(self, user_id: str, role: MessageRole, content: str):
        self.user_id = user_id
        self.role = role
        self.content = content
