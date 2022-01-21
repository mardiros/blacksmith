from blacksmith import PathInfoField, register, Request, Response


class UserRequest(Request):
    username: str = PathInfoField()


class User(Response):
    email: str
    firstname: str
    lastname: str


register(
    client_name="api_user",
    resource="users",
    service="user",
    version="v1",
    path="/users/{username}",
    contract={
        "GET": (UserRequest, User),
    },
)
