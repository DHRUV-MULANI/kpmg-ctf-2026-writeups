from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")

async def parse_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET,
                          algorithms=[settings.ALGORITHM],
                          options={"verify_aud": False})
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")
