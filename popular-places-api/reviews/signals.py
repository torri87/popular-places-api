from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from locations.cache_utils import bump_locations_cache_version
from .models import Review


@receiver([post_save, post_delete], sender=Review)
def invalidate_locations_cache_on_review_change(sender, instance, **kwargs):
    bump_locations_cache_version()