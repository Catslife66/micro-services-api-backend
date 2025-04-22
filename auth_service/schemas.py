from ninja import ModelSchema, Schema
from typing_extensions import Annotated
from pydantic import  EmailStr, AfterValidator
from ninja_jwt.schema import TokenObtainPairInputSchema

from .models import AppUser
from .validators import check_password_strength


class UserSchema(ModelSchema):
    class Meta:
        model = AppUser
        fields = ('id', 'username', 'email')


class UserIn(Schema):
    email: EmailStr
    username: str
    password: Annotated[str, AfterValidator(check_password_strength)]


class UserOut(Schema):
    id: int
    username: str
    email: EmailStr


class ErrorUserSchema(Schema):
    error: str


class PasswordForgotSchema(Schema):
    email: EmailStr


class PasswordResetSchema(Schema):
    uidb64: str
    token: str
    email: EmailStr
    password: Annotated[str, AfterValidator(check_password_strength)]


class MyTokenObtainPairOutSchema(Schema):
    refresh: str
    access: str
    user: UserSchema


class MyTokenObtainPairSchema(TokenObtainPairInputSchema):
    def output_schema(self):
        out_dict = self.get_response_schema_init_kwargs()
        out_dict.update(user=UserSchema.from_orm(self._user))
        return MyTokenObtainPairOutSchema(**out_dict)
