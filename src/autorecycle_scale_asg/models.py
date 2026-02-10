from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class MessageContent(BaseModel):
    color: str
    text: str
    fields: Optional[List[Dict[str, Any]]] = None
