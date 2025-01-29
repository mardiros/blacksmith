from pathlib import Path

import unasync  # type: ignore

DIRECTORIES = [
    "src/blacksmith/middleware/_async",
    "src/blacksmith/sd/_async",
    "src/blacksmith/sd/_async/adapters",
    "src/blacksmith/service/_async",
    "src/blacksmith/service/_async/adapters",
]

for path in DIRECTORIES:
    unasync.unasync_files(
        [str(p) for p in Path(path).iterdir() if p.is_file()],
        rules=[
            unasync.Rule(
                path,
                path.replace("_async", "_sync"),
                additional_replacements={
                    "_async": "_sync",
                    "asyncio": "client",  # replace redis.asyncio -> redis.client
                    "AsyncHTTPTransport": "HTTPTransport",
                },
            ),
        ],
    )


unasync.unasync_files(
    [str(p) for p in Path("tests/unittests/_async").iterdir() if p.is_file()],
    rules=[
        unasync.Rule(
            "tests/unittests/_async",
            "tests/unittests/_sync",
            additional_replacements={
                "_async": "_sync",
                "AsyncSleep": "SyncSleep",
                "httpx._client.AsyncClient.request": "httpx._client.Client.request",
                "AsyncHTTPTransport": "HTTPTransport",
            },
        ),
    ],
)
