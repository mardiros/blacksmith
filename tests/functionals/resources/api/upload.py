from pydantic import BaseModel

from blacksmith import (
    Attachment,
    AttachmentField,
    PostBodyField,
    Request,
    Response,
    register,
)


class UploadRequest(Request):
    foobar: str = PostBodyField()
    attachmt: Attachment = AttachmentField()


class UploadQuery(BaseModel):
    name: str
    value: int


class UploadComplexRequest(Request):
    foobar: UploadQuery = PostBodyField()
    attachmt: Attachment = AttachmentField()


class UploadedFile(Response):
    foobar: str
    filename: str
    content: str


register(
    client_name="api",
    resource="upload",
    service="api",
    version=None,
    path="/upload",
    contract={
        "POST": (UploadRequest, UploadedFile),
    },
)

register(
    client_name="api",
    resource="upload_complex",
    service="api",
    version=None,
    path="/upload-complex",
    contract={
        "POST": (UploadComplexRequest, UploadedFile),
    },
)
