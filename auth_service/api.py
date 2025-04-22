from typing import List
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.core.mail import send_mail
from django.http.response import JsonResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import get_object_or_404, redirect
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth
from ninja.security import django_auth

from .schemas import UserSchema, UserIn, UserOut, ErrorUserSchema, PasswordForgotSchema, PasswordResetSchema
from .models import AppUser

@api_controller('/users', tags=['Auth'])
class UserController:
    @route.get('/', response=List[UserSchema])
    def get_users(self):
        return AppUser.objects.all()
    
    @route.get('/me', response={200:UserOut, 400:ErrorUserSchema}, auth=[JWTAuth(), django_auth])
    def get_me(self, request):
        try:
            user = AppUser.objects.get(id=request.auth.id)
            return 200, user
        except Exception as e:
            return 400, {'error': str(e)}
    
    @route.post('/register', response={201: UserOut, 400: ErrorUserSchema})
    def register_user(self, payload: UserIn):
        if AppUser.objects.filter(email=payload.email).exists():
            return 400, {'error': "This email has been registeredd."}

        try:
            password = make_password(payload.password)
            user = AppUser.objects.create(email=payload.email, username=payload.username, password=password)
            return 201, user
        except Exception as e:
            return 400, {'error': str(e)}
        
    
    @route.post('/forgot-password', response={200: PasswordForgotSchema, 400: ErrorUserSchema})
    def forget_password(self, payload:PasswordForgotSchema):
        email = payload.email
        try:
            user = AppUser.objects.get(email=email)
            uid = urlsafe_base64_encode(str(user.id).encode())
            token = default_token_generator.make_token(user)
            
            #{{ protocol}}://{{ domain }}{% url 'password_reset_confirm' uidb64=uid token=token %}
            frontend_url = settings.CORS_ALLOWED_ORIGINS[0]
            reset_link = f"{frontend_url}/reset-password?uidb64={uid}&token={token}"
            
            send_mail(
                "Password Reset Request",
                f"Click the link below to reset your password:\n\n{reset_link}",
                "noreply@yourapp.com",
                [email],
                fail_silently=False,
            )
            return 200, {'email': user.email}

        except Exception as e:
            return 400, {'error': str(e)}
        

    @route.post('/reset-password', response={200: PasswordResetSchema, 400: ErrorUserSchema})
    def reset_password(self, payload:PasswordResetSchema):
        uidb64 = payload.uidb64
        token = payload.token
        if not uidb64 or not token:
            return JsonResponse({'error': "The URL path must contain 'uidb64' and 'token' parameters."})
        
        try:
            try:
                uid = int(urlsafe_base64_decode(uidb64).decode())  
            except (TypeError, ValueError, OverflowError):
                return JsonResponse({"error": "Invalid UID. Please resend your reset password request."}, status=400)
            
            user = get_object_or_404(AppUser, id=uid)
            if user.email.lower() != payload.email.lower():
                return JsonResponse({"error": "The email address entered does not match the email address that the password reset instructions were sent to."}, status=400)
            
            isValidToken= default_token_generator.check_token(user, token)
            if not isValidToken:
                return JsonResponse({"error": "Invalid or expired reset token. Please resend your reset password request."}, status=400)

            user.set_password(payload.password)
            user.save()
            return JsonResponse({"email": user.email, 'username': user.username}, status=200)

        except Exception as e:
            return 400, {'error': str(e)}
        
