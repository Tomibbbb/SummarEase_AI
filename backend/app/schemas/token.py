from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    """
    Schema for access token response.
    """
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """
    Schema for JWT token payload.
    """
    sub: Optional[int] = None