from blacksmith import Attachment, AttachmentField, PostBodyField, Request


class UploadRequest(Request):
    foobar: str = PostBodyField()
    attachmt: Attachment = AttachmentField()
