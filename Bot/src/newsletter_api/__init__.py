"""
Newsletter API Internal Module
Внутренний модуль Newsletter API для Torah Bot
"""

from .service import NewsletterAPIService, get_newsletter_service, cleanup_newsletter_service
from .client import InternalNewsletterAPIClient, send_newsletter_broadcast, get_newsletter_stats, send_quiz_to_admin

__all__ = [
    'NewsletterAPIService',
    'get_newsletter_service', 
    'cleanup_newsletter_service',
    'InternalNewsletterAPIClient',
    'send_newsletter_broadcast',
    'get_newsletter_stats',
    'send_quiz_to_admin'
]