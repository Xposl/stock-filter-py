from typing import Optional

from pydantic import BaseModel


class PageRequest(BaseModel):
    page: int = 1
    page_size: int = 10
    search: Optional[str] = None
    sort: Optional[list[str]] = None
