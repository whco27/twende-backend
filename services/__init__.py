"""Services package - business logic and external integrations"""
from .notifications import NotificationService, mail

__all__ = ['NotificationService', 'mail']
