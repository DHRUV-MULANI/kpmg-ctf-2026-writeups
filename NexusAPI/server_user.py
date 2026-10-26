import time, uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt
from app.core.config import settings

router = APIRouter(tags=["user"])

USERS: dict = {}  # email -> {password, guid}

class SignupBody(BaseModel):
    email: str
    password: str

@router.post("/signup", status_code=201)
def signup(body: SignupBody):
    if body.email in USERS:
        raise HTTPException(400, "Email taken")
    USERS[body.email] = {"password": body.password, "guid": str(uuid.uuid4())}
    return {}

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form.username)
    if not user or user["password"] != form.password:
        raise HTTPException(401, "Bad credentials")
    payload = {
        "sub": form.username,
        "guid": user["guid"],
        "debug": False,
        "exp": int(time.time()) + 86400,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# Intentional debug route that leaks the signing key hint
@router.get("/source")
def source():
    """Returns sanitised app config — left in by accident during development."""
    return {
        "app": "NexusAPI",
        "algorithm": settings.ALGORITHM,
        # oops — dev left this in
        "signing_key": settings.JWT_SECRET,
    }
