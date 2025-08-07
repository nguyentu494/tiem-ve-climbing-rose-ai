from sqlalchemy import Column, Integer, String
from app.models.base_model import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship



class User(Base):
    __tablename__ = 'users'  
    __table_args__ = {'extend_existing': True}

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)    
