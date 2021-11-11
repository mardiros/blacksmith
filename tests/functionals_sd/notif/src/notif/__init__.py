from typing import cast

import uvicorn
from asgiref.typing import ASGI3Application
from pydantic.fields import Field
from starlette.applications import Starlette
from starlette.responses import JSONResponse

import aioli
from aioli import (
    ClientFactory,
    ConsulDiscovery,
    PathInfoField,
    Request,
    Response,
    StaticDiscovery,
)

app = Starlette(debug=True)


class UserRequest(Request):
    username: str = PathInfoField()


class User(Response):
    email: str
    firstname: str
    lastname: str


aioli.register(
    "api_user", "users", "user", "v1", "/users/{username}", {"GET": (UserRequest, User)}
)
# sd = StaticDiscovery({("user", "v1"): "http://api_user:8000/v1"})
sd = ConsulDiscovery()
cli = ClientFactory(sd)


@app.route("/v1/notification", methods=["POST"])
async def show_user(request):
    body = await request.json()
    api_user = await cli("api_user")
    user = cast(User, await api_user.users.get(UserRequest(username=body["username"])))
    return JSONResponse({"detail": f"{user.email} accepted"}, status_code=202)


if __name__ == "__main__":
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)
