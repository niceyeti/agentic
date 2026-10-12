from pydantic import BaseModel, Field


class Config(BaseModel):
    """Config."""

    foo = Field(default="abc", min_length=1)
