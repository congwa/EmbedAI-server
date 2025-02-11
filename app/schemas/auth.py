from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Form
from pydantic import EmailStr

class OAuth2EmailPasswordRequestForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        email: EmailStr = Form(...),  # 使用 EmailStr 进行邮箱格式验证
        password: str = Form(...),
        scope: str = Form(""),
        client_id: str | None = Form(None),
        client_secret: str | None = Form(None),
    ):
        super().__init__(
            username=email,  # 将email赋值给父类的username
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret
        )
        self.email = email  # 添加email属性 