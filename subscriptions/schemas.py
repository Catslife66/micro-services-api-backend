from datetime import datetime
from ninja import Schema
from typing import List, Optional
from pydantic import Field
from subscriptions.models import UserSubscription


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


class UserSubscriptionSchema(Schema):
    id: int
    subscription: str
    stripe_id: str
    status: str
    price: float
    interval: str
    created_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    is_allow_to_cancel: bool
    is_cancelled: bool
    cancelled_at: Optional[datetime] = None


class UserCancelSubscriptionSchema(Schema):
    stripe_id: str
    cancel_at_period_end: bool

class UserCancelSubscriptionErrorSchema(Schema):
    error: str