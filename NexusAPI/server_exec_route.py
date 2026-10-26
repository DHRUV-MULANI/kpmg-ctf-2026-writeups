import subprocess
from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import parse_token
from app.core.config import settings

router = APIRouter(tags=["exec"])

@router.get("/{command:path}")
def run(command: str, current_user: dict = Depends(parse_token)):
    """Run a shell command. Requires debug:true in JWT."""
    if not current_user.get("debug"):
        raise HTTPException(400, "Debug claim missing or false in JWT")
    out = subprocess.run(
        ["/bin/sh", "-c", command],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
    ).stdout.decode().strip()
    # Flag lives in env
    return {"output": out}
