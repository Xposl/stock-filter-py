from pydantic import BaseModel
from typing import Optional

class PageRequest(BaseModel):
    page: int = 1
    page_size: int = 10
    search: Optional[str] = None
