import email as emaillib
import smtplib
from textwrap import dedent

from notif.resources.user import User
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette_zipkin import trace

from blacksmith import AsyncClientFactory, AsyncConsulDiscovery
from blacksmith.domain.exceptions import HTTPError
from blacksmith.middleware._async.zipkin import (
    AbtractTraceContext,
    AsyncZipkinMiddleware,
)

AbtractTraceContext.register(trace)


app = Starlette(debug=True)

smtp_sd = AsyncConsulDiscovery()

sd = AsyncConsulDiscovery()
cli = AsyncClientFactory(sd).add_middleware(AsyncZipkinMiddleware(trace))


@trace("send email")
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
    try:
        user: User = (await api_user.users.get({"username": body["username"]})).response
    except HTTPError as exc:
        status_code = exc.response.status_code
        resp = exc.response.json
    else:
        await send_email(user, body["message"])
        status_code = 202
        resp = {"detail": f"{user.email} accepted"}

    return JSONResponse(
        resp,
        status_code=status_code,
    )
