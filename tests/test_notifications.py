"""Tests for notification service"""
import pytest
from unittest.mock import patch, MagicMock


def test_notification_service_disabled_without_config(client):
    """Test notification service is disabled when email not configured"""
    from services.notifications import notification_service
    # In test environment, email is not configured
    assert notification_service.enabled is False


def test_send_registration_confirmation_disabled(client, sample_user):
    """Test registration confirmation skips when email disabled"""
    from services.notifications import notification_service
    from app import app, db
    from models import User

    with app.app_context():
        user = db.session.get(User, sample_user)
        result = notification_service.send_registration_confirmation(user)
        # Should return False when email is disabled
        assert result is False


def test_notify_admin_disabled(client, sample_user):
    """Test admin notification skips when email disabled"""
    from services.notifications import notification_service
    from app import app, db
    from models import User

    with app.app_context():
        user = db.session.get(User, sample_user)
        result = notification_service.notify_admin_new_registration(user)
        # Should return False when email is disabled
        assert result is False


def test_get_admin_emails_empty():
    """Test admin emails returns empty list when not configured"""
    from services.notifications import notification_service
    import os

    # Clear any existing ADMIN_EMAILS
    original = os.environ.get('ADMIN_EMAILS')
    if 'ADMIN_EMAILS' in os.environ:
        del os.environ['ADMIN_EMAILS']

    try:
        emails = notification_service._get_admin_emails()
        assert emails == []
    finally:
        if original:
            os.environ['ADMIN_EMAILS'] = original


def test_get_admin_emails_configured():
    """Test admin emails parses comma-separated values"""
    from services.notifications import notification_service
    import os

    original = os.environ.get('ADMIN_EMAILS')
    os.environ['ADMIN_EMAILS'] = 'admin1@test.com, admin2@test.com , admin3@test.com'

    try:
        emails = notification_service._get_admin_emails()
        assert len(emails) == 3
        assert 'admin1@test.com' in emails
        assert 'admin2@test.com' in emails
        assert 'admin3@test.com' in emails
    finally:
        if original:
            os.environ['ADMIN_EMAILS'] = original
        else:
            del os.environ['ADMIN_EMAILS']


def test_registration_triggers_notifications(client):
    """Test that registration attempts to send notifications"""
    from services.notifications import notification_service

    # Mock the notification methods to track calls
    with patch.object(
        notification_service, 'send_registration_confirmation', return_value=False
    ) as mock_confirmation, \
         patch.object(
             notification_service, 'notify_admin_new_registration', return_value=False
         ) as mock_admin:

        user_data = {
            'email': 'notify_test@example.com',
            'password': 'securepass123',
            'first_name': 'Notify',
            'last_name': 'Test'
        }
        response = client.post('/api/auth/register', json=user_data)

        assert response.status_code == 201
        # Verify notification methods were called
        mock_confirmation.assert_called_once()
        mock_admin.assert_called_once()


def test_registration_succeeds_even_if_notifications_fail(client):
    """Test that registration succeeds even when notifications raise exceptions"""
    from services.notifications import notification_service

    # Mock notification methods to raise exceptions
    with patch.object(
        notification_service, 'send_registration_confirmation',
        side_effect=Exception('Email failed')
    ), patch.object(
        notification_service, 'notify_admin_new_registration',
        side_effect=Exception('Admin notification failed')
    ):

        user_data = {
            'email': 'exception_test@example.com',
            'password': 'securepass123',
            'first_name': 'Exception',
            'last_name': 'Test'
        }
        response = client.post('/api/auth/register', json=user_data)

        # Registration should still succeed
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['user']['email'] == 'exception_test@example.com'
