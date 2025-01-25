from typing import Optional
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    username: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }
