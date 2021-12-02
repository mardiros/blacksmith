import email as emaillib
import smtplib
from textwrap import dedent
from typing import Dict, cast

import aiozipkin
from aiozipkin.helpers import make_headers
from starlette.applications import Starlette
from starlette.responses import JSONResponse

import aioli
from aioli import ClientFactory, ConsulDiscovery
from aioli.domain.model import HTTPAuthentication

from notif.resources.user import User
from notif.zk_middleware import Trace

app = Starlette(debug=True)

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
    cli = cast(ClientFactory, request.scope.get("aioli_client"))
    body = await request.json()

    root_trace: Trace = request.scope["trace"]

    async with root_trace.new_child("resolve_api_user") as trace:
        api_user = await cli("api_user")

    async with trace.new_child("get_user"):
        user: User = (
            await api_user.users.get({"username": body["username"]})
        ).response

    async with root_trace.new_child("send_email"):
        await send_email(user, body["message"])

    return JSONResponse(
        {"detail": f"{user.email} accepted"},
        status_code=202,
    )
