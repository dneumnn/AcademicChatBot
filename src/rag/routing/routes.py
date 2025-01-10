from typing import Literal
from pydantic import BaseModel, Field

SUBJECTS = ["physics", "math", "chemistry", "biology", "history", "geography", 
            "literature", "art", "music", "philosophy", "psychology", 
            "economics", "politics", "religion", "other"]

class RouteQuery(BaseModel):
    """Detect the subject of the query"""

    subject: Literal["physics", "math", "chemistry", "biology", "history", "geography", 
                     "literature", "art", "music", "philosophy", "psychology", 
                     "economics", "politics", "religion", "other"] = Field(
        ...,
        description="Given a user question, determine the subject of the question"
    )