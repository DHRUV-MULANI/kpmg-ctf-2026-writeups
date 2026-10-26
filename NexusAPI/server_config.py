import os

class Settings:
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "y0u_f0und_th3_k3y")
    ALGORITHM: str  = "HS256"
    FLAG: str       = os.environ.get("FLAG", "KPMG_CTF{find_me_if_you_can}")

settings = Settings()
