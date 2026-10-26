from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.v1.endpoints import user, exec_route

app = FastAPI(title="NexusAPI", version="1.3", docs_url="/docs", redoc_url=None)

@app.get("/")
def index():
    return {"msg": "NexusAPI v1.3 — /api/v1"}

@app.get("/api/v1")
def v1_index():
    return {"endpoints": ["user", "exec"]}

app.include_router(user.router,       prefix="/api/v1/user")
app.include_router(exec_route.router, prefix="/api/v1/exec")
app.include_router(exec_route.router, prefix="/api/v1//exec")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="NexusAPI",
        version="1.3",
        description="""
## NexusAPI v1.3 — Internal Document Management

### Endpoints
- **user** — register, login, profile
- **exec** — command execution (debug access required)

> ⚠️ The `/exec` endpoint is restricted. Auth via Bearer JWT.
        """,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
