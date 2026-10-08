import logging

from django.conf import settings

from . import encryption
from .models import AuditLog

logger = logging.getLogger(__name__)


def client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()[:45]
    return request.META.get('REMOTE_ADDR') or None


def log_event(action, user=None, request=None, status_code=None, detail='', subject_plain=None):
    if not settings.AUDIT_LOG_ENABLED:
        return
    try:
        AuditLog.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            action=action,
            method=request.method[:10] if request else '',
            path=request.path[:255] if request else '',
            ip=client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT', '') or '')[:256] if request else '',
            status_code=status_code,
            detail=detail[:500],
            subject_enc=encryption.encrypt(subject_plain) if subject_plain else '',
        )
    except Exception:
        logger.exception('Falha ao gravar audit log (action=%s)', action)
