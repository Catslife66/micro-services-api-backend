from ninja_extra import NinjaExtraAPI, api_controller, route
from ninja_jwt.controller import TokenObtainPairController, TokenVerificationController
from auth_service.api import UserController
from auth_service.schemas import MyTokenObtainPairSchema, MyTokenObtainPairOutSchema
from payments.api import PaymentController
from subscriptions.api import SubscriptionController

api = NinjaExtraAPI()

@api_controller('/token', tags=['Auth'])
class MyNinjaJwtController(TokenObtainPairController, TokenVerificationController):
    # login
    @route.post(
        "/pair", response=MyTokenObtainPairOutSchema, url_name="token_obtain_pair"
    )
    def obtain_token(self, user_token: MyTokenObtainPairSchema):
        return user_token.output_schema()


api.register_controllers(
    MyNinjaJwtController, 
    PaymentController,
    UserController, 
    SubscriptionController
)