import email as emaillib
import smtplib
from textwrap import dedent

from notif.resources.user import User
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from purgatory import AsyncRedisUnitOfWork
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response

from blacksmith import (
    AsyncCircuitBreakerMiddleware,
    AsyncClientFactory,
    AsyncConsulDiscovery,
    AsyncPrometheusMiddleware,
    PrometheusMetrics,
)

app = Starlette(debug=True)

sd = AsyncConsulDiscovery()
metrics = PrometheusMetrics()
cli = (
    AsyncClientFactory(sd)
    .add_middleware(
        AsyncCircuitBreakerMiddleware(
            3,
            30,
            metrics=metrics,
            uow=AsyncRedisUnitOfWork("redis://redis/0"),
        ),
    )
    .add_middleware(AsyncPrometheusMiddleware(metrics))
)


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

    srv = await sd.resolve("smtp", None)
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
    user: User = (await api_user.users.get({"username": body["username"]})).unwrap()
    await send_email(user, body["message"])
    return JSONResponse({"detail": f"{user.email} accepted"}, status_code=202)


@app.route("/metrics", methods=["GET"])
async def get_metrics(request):
    resp = Response(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
    return resp
