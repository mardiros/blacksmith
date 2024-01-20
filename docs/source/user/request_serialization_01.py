from blacksmith import HeaderField, PostBodyField, Request


class MyFormURLEncodedRequest(Request):
    foo: str = PostBodyField()
    bar: int = PostBodyField()
    content_type: str = HeaderField(
        "application/x-www-form-urlencoded", alias="Content-Type"
    )
