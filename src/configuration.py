import sys
from typing import Optional

from pydantic import BaseModel, validator


class Configuration(BaseModel):
    mlol_website: str
    mlol_username: str
    mlol_password: str

    pressreader_username: str
    pressreader_password: str

    telegram_base_url: Optional[str]
    telegram_token: Optional[str]
    telegram_chat_id: Optional[int]

    @validator("mlol_website")
    def mlol_website_must_have_mlol_subdomain(cls, website) -> Optional[str]:
        if "medialibrary.it" not in website:
            sys.exit("MLOL website sanitation failed!")
        return website
