from .user import User
from .message import ChatMessage
from sqlalchemy.orm import relationship

# Định nghĩa relationship sau cùng để tránh vòng lặp
User.messages = relationship("ChatMessage", back_populates="user")
ChatMessage.user = relationship("User", back_populates="messages")
