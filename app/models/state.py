from typing import TypedDict, List, Any
from app.models.extract_param import SearchParams
from pydantic import BaseModel, Field
from langchain.schema import Document


class State(BaseModel):
    chat_id: str = ""
    user_input: str = ""
    chat_history: List[str] = Field(default_factory=list)
    context: List[str] | str = ""
    final_generation: str = ""
    error: List[str] = Field(default_factory=list)
    next_state: str = ""
    user_id: str = ""
    search_params: SearchParams = Field(default_factory=SearchParams)