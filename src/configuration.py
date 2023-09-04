import sys
from typing import Optional

from pydantic import BaseModel, field_validator


class Configuration(BaseModel):
    mlol_website: str
    mlol_username: str
    mlol_password: str

    pressreader_username: str
    pressreader_password: str

    telegram_base_url: Optional[str] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[int] = None

    @field_validator("mlol_website")
    @classmethod
    def mlol_website_must_have_mlol_subdomain(cls, website) -> Optional[str]:
        if "medialibrary.it" not in website:
            sys.exit("MLOL website sanitation failed!")
        return website
