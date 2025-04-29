from django.db import models
from django.conf import settings

import helpers.billing

User = settings.AUTH_USER_MODEL

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.stripe_id:
            stripe_id = helpers.billing.create_custome(
                name=self.user.username, 
                email=self.user.email, 
                metadata={'user_id': self.user.id}
                )
            self.stripe_id = stripe_id

        super().save(*args, **kwargs)

