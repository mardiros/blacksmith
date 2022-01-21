import uvicorn
from notif.views import app

import blacksmith

if __name__ == "__main__":
    blacksmith.scan("notif.resources")
    uvicorn.run(app, host="0.0.0.0", port=8000)
