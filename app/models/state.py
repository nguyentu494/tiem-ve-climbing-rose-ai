from typing import TypedDict, List, Any
from app.models.extract_param import SearchParams
from pydantic import BaseModel, Field
from langchain.schema import Document
from langchain_core.messages import HumanMessage, AIMessage


class State(BaseModel):
    chat_id: str = ""
    user_input: str = ""
    chat_history: List[HumanMessage | AIMessage] = Field(default_factory=list)
    context: List[str] | str = ""
    final_generation: str = ""
    error: List[str] = Field(default_factory=list)
    is_relevant: bool = True
    next_state: str = ""
    user_id: str = ""
    last_keywords: List[str] = []  
    search_params: SearchParams = Field(default_factory=SearchParams)