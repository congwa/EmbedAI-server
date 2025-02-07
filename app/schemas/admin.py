from pydantic import BaseModel

class AdminRegister(BaseModel):
    email: str
    password: str
    register_code: str  # 管理员注册码，用于验证是否有权限注册管理员账户