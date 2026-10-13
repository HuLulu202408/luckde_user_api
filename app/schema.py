from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    account: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    nickname: str | None = Field(default=None, max_length=100)
    mail: str | None = Field(default=None, max_length=100)
    gender: int = Field(default=0, ge=0, le=2)

    deviceid: str | None = Field(default=None, max_length=100)
    channel: str | None = Field(default=None, max_length=100)
    platform: str | None = Field(default=None, max_length=100)
    schema: str | None = Field(default=None, max_length=100)
    version: str | None = Field(default=None, max_length=100)
    version_code: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class SocialLoginRequest(BaseModel):
    id_token: str = Field(min_length=1)
    deviceid: str | None = Field(default=None, max_length=100)
    channel: str | None = Field(default=None, max_length=100)
    platform: str | None = Field(default=None, max_length=100)
    version: str | None = Field(default=None, max_length=100)
    version_code: str | None = Field(default=None, max_length=100)