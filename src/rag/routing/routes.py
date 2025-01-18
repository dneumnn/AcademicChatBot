from typing import Literal
from pydantic import BaseModel, Field, field_validator

from ..vectorstore.vectorstore import get_vector_collections

SUBJECTS = get_vector_collections()

class RouteQuery(BaseModel):
    """Detect the subject of the query"""

    subject: Literal[*SUBJECTS] = Field( # type: ignore
        ...,
        description="Given a user question, determine the subject of the question"
    )

    @field_validator('subject')
    def validate_subject(cls, v):
        if v not in SUBJECTS:
            raise ValueError(f"Subject must be one of {SUBJECTS}")
        return v