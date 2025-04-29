from typing import List
from ninja import Schema


class SubscriptionPlanPriceOutSchema(Schema):
    id: int
    price: float
    interval: str
    stripe_id: str


class SubscriptionPlanOutSchema(Schema):
    id: int
    name: str
    descriptions: str
    prices: List[SubscriptionPlanPriceOutSchema]
    stripe_id: str

