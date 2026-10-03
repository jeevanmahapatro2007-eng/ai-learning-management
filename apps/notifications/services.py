from .models import Notification


def notify(user, title, message, category=Notification.Category.SYSTEM, link=''):
    """Central helper used across the platform to raise a notification (section 15)."""
    return Notification.objects.create(
        user=user, title=title[:150], message=message[:300], category=category, link=link,
    )
