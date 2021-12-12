import email as emaillib
import smtplib
from textwrap import dedent
from typing import cast

import uvicorn
from asgiref.typing import ASGI3Application
from notif.resources.user import User
from starlette.applications import Starlette
from starlette.responses import JSONResponse

import blacksmith
from blacksmith import ClientFactory, ConsulDiscovery, RouterDiscovery

app = Starlette(debug=True)

blacksmith.scan("notif.resources")
sd = RouterDiscovery()
cli = ClientFactory(sd)


smtp_sd = ConsulDiscovery()


async def send_email(user: User, message: str):
    email_content = dedent(
        f"""\
        Subject: notification
        From: notification@localhost
        To: "{user.firstname} {user.lastname}" <{user.email}>

        {message}
        """
    )
    msg = emaillib.message_from_string(email_content)

    srv = await smtp_sd.resolve("smtp", None)
    # XXX Synchronous socket here, OK for the example
    # real code should use aiosmtplib
    s = smtplib.SMTP(srv.address, int(srv.port))
    s.send_message(msg)
    s.quit()


@app.route("/v1/notification", methods=["GET"])
async def get_notif(request):
    return JSONResponse({"detail": "Use POST"}, status_code=200)


@app.route("/v1/notification", methods=["POST"])
async def post_notif(request):
    body = await request.json()
    api_user = await cli("api_user")
    user: User = (await api_user.users.get({"username": body["username"]})).response
    await send_email(user, body["message"])
    return JSONResponse({"detail": f"{user.email} accepted"}, status_code=202)


if __name__ == "__main__":
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)
