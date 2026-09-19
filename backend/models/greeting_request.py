from typing import Optional
from pydantic import BaseModel

class GreetingRequest(BaseModel):
    session_id: Optional[str] = None