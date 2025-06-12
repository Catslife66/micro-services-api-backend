from ninja import Schema
from pydantic import EmailStr


class CheckoutSessionIn(Schema):
    useremail: EmailStr
    price_id: str