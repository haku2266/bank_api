from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
from pathlib import Path

BASE_DIR = Path(__file__).parent


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    algorith: str = "RS256"
    access_token_exp_minutes: int = 30


class Settings(BaseSettings):
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    EMAIL_USER: str
    EMAIL_PASS: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    REDIS_HOST: str
    REDIS_PORT: str
    AUTH_JWT: AuthJWT = AuthJWT()

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # @property
    # def DATABASE_URL_psycopg(self):
    #     return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
