from blacksmith import Request, HeaderField, PostBodyField


class MyFormURLEncodedRequest(Request):
    foo: str = PostBodyField()
    bar: int = PostBodyField()
    content_type: str = HeaderField(
        "application/x-www-form-urlencoded", alias="Content-Type"
    )
