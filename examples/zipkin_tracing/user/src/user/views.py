import json

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette_zipkin import B3Headers, ZipkinConfig, ZipkinMiddleware

app = Starlette(debug=True)
config = ZipkinConfig(
    host="zipkin",
    port=9411,
    service_name="user-v1",
    sample_rate=1.0,
    inject_response_headers=True,
    force_new_trace=False,
    json_encoder=json.dumps,
    header_formatter=B3Headers,
)
app.add_middleware(ZipkinMiddleware, config=config)

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
