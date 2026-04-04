from pydantic import BaseModel


class UploadResponse(BaseModel):
    blueprint_id: str
