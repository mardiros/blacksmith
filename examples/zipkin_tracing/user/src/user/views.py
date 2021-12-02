from typing import cast
from asgiref.typing import ASGI3Application
import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse

app = Starlette(debug=True)

USERS = {
    "naruto": {
        "username": "naruto",
        "firstname": "Naruto",
        "lastname": "Uzumaki",
        "email": "naruto@konoa.city",
        "roles": ["genin"],
    },
    "hinata": {
        "username": "hinata",
        "firstname": "Hinata",
        "lastname": "Hyûga",
        "email": "hinata@konoa.city",
        "roles": ["chunin"],
    },
}


@app.route("/v1/users/{username}", methods=["GET"])
async def show_user(request):
    username = request.path_params["username"]
    try:
        return JSONResponse(USERS[username])
    except KeyError:
        return JSONResponse({"detail": "user not found"}, status_code=404)
