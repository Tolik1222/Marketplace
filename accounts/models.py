from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class SellerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_profile')
    stripe_account_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Nova Poshta sender settings
    np_sender_ref = models.CharField(max_length=100, blank=True, null=True)
    np_sender_address_ref = models.CharField(max_length=100, blank=True, null=True)
    np_sender_contact_ref = models.CharField(max_length=100, blank=True, null=True)
    np_sender_phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Seller Profile for {self.user.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_seller_profile(sender, instance, created, **kwargs):
    if created:
        SellerProfile.objects.get_or_create(user=instance)
    else:
        if not hasattr(instance, 'seller_profile'):
            SellerProfile.objects.get_or_create(user=instance)