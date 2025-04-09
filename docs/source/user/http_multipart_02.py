from pydantic import BaseModel

from blacksmith import Attachment, AttachmentField, PostBodyField, Request


class Query(BaseModel):
    name: str
    version: int


class UploadRequest(Request):
    query: Query = PostBodyField()
    attachmt: Attachment = AttachmentField()
