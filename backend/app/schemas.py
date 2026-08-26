from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    is_admin: bool


class CheckResult(BaseModel):
    label: str
    passed: bool
    message: str


class CheckResponse(BaseModel):
    passed: bool
    results: list[CheckResult]


class SelectResponse(BaseModel):
    created_files: list[str]


class FileEntry(BaseModel):
    path: str
    type: str


class FileContentIn(BaseModel):
    path: str
    content: str
