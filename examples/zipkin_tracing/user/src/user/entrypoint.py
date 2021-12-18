from typing import cast

import uvicorn
from asgiref.typing import ASGI3Application
from user.views import app

if __name__ == "__main__":
    uvicorn.run(cast(ASGI3Application, app), host="0.0.0.0", port=8000)
