from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from notif.config import FastConfig, AppConfig
from notif.resources.user import User

from blacksmith import AsyncClientFactory, AsyncConsulDiscovery, AsyncRouterDiscovery

fastapi = FastAPI()


@fastapi.api_route("/v1/notification", methods=["POST"])
async def post_notif(
    request: Request,
    app: AppConfig = FastConfig.depends,
):
    body = await request.json()
    api_user = await app.get_client("api_user")
    user: User = (await api_user.users.get({"username": body["username"]})).response
    #  await send_email(user, body["message"])
    return JSONResponse({"detail": f"{user.email} accepted"}, status_code=202)
