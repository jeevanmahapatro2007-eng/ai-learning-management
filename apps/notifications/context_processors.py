def unread_notifications(request):
    if not request.user.is_authenticated:
        return {}
    qs = request.user.notifications.filter(is_read=False)
    return {
        'unread_notification_count': qs.count(),
        'latest_notifications': qs[:5],
    }
