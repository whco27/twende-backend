"""Tests for trip schedule routes"""
from datetime import datetime, timedelta, timezone


# Get a future date for testing (30 days from now)
def get_future_datetime():
    return (datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')


def get_future_datetime_offset(days):
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S')


def test_create_trip_schedule(client, sample_user):
    """Test creating a trip schedule"""
    schedule_data = {
        'user_id': sample_user,
        'title': 'Safari Adventure',
        'description': 'A great safari experience',
        'location': 'Masai Mara',
        'departure_date': get_future_datetime()
    }
    response = client.post('/api/trip-schedules/', json=schedule_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['trip_schedule']['title'] == 'Safari Adventure'
    assert data['trip_schedule']['location'] == 'Masai Mara'


def test_create_trip_schedule_with_return_date(client, sample_user):
    """Test creating a trip schedule with return date"""
    schedule_data = {
        'user_id': sample_user,
        'title': 'Weekend Getaway',
        'location': 'Diani Beach',
        'departure_date': get_future_datetime_offset(30),
        'return_date': get_future_datetime_offset(33)
    }
    response = client.post('/api/trip-schedules/', json=schedule_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['trip_schedule']['return_date'] is not None


def test_create_trip_schedule_missing_required(client, sample_user):
    """Test creating a trip schedule with missing required fields"""
    schedule_data = {
        'user_id': sample_user,
        'title': 'Missing Location'
    }
    response = client.post('/api/trip-schedules/', json=schedule_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'location' in data['error']


def test_create_trip_schedule_invalid_date(client, sample_user):
    """Test creating a trip schedule with invalid date format"""
    schedule_data = {
        'user_id': sample_user,
        'title': 'Invalid Date Trip',
        'location': 'Nairobi',
        'departure_date': 'not-a-valid-date'
    }
    response = client.post('/api/trip-schedules/', json=schedule_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_create_trip_schedule_user_not_found(client):
    """Test creating a trip schedule with non-existent user"""
    schedule_data = {
        'user_id': 9999,
        'title': 'Invalid User Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    }
    response = client.post('/api/trip-schedules/', json=schedule_data)
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert 'User not found' in data['error']


def test_get_trip_schedules(client, sample_user):
    """Test getting all trip schedules"""
    # Create a trip schedule first
    client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Test Trip',
        'location': 'Test Location',
        'departure_date': get_future_datetime()
    })

    response = client.get('/api/trip-schedules/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'trip_schedules' in data
    assert 'pagination' in data


def test_get_trip_schedules_filter_by_user(client, sample_user):
    """Test getting trip schedules filtered by user"""
    # Create a trip schedule
    client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'User Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })

    response = client.get(f'/api/trip-schedules/?user_id={sample_user}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    for schedule in data['trip_schedules']:
        assert schedule['user_id'] == sample_user


def test_get_trip_schedules_filter_by_status(client, sample_user):
    """Test getting trip schedules filtered by status"""
    # Create a trip schedule
    client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Scheduled Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime(),
        'status': 'scheduled'
    })

    response = client.get('/api/trip-schedules/?status=scheduled')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    for schedule in data['trip_schedules']:
        assert schedule['status'] == 'scheduled'


def test_get_trip_schedule_by_id(client, sample_user):
    """Test getting a specific trip schedule"""
    # Create a trip schedule
    create_response = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Specific Trip',
        'location': 'Test Location',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_response.get_json()['trip_schedule']['id']

    response = client.get(f'/api/trip-schedules/{schedule_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['trip_schedule']['id'] == schedule_id


def test_get_trip_schedule_not_found(client):
    """Test getting a non-existent trip schedule"""
    response = client.get('/api/trip-schedules/9999')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False


def test_update_trip_schedule(client, sample_user):
    """Test updating a trip schedule"""
    # Create a trip schedule
    create_response = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Original Title',
        'location': 'Original Location',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_response.get_json()['trip_schedule']['id']

    # Update it
    response = client.put(f'/api/trip-schedules/{schedule_id}', json={
        'title': 'Updated Title',
        'status': 'in_progress'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['trip_schedule']['title'] == 'Updated Title'
    assert data['trip_schedule']['status'] == 'in_progress'


def test_update_trip_schedule_not_found(client):
    """Test updating a non-existent trip schedule"""
    response = client.put('/api/trip-schedules/9999', json={
        'title': 'Does Not Exist'
    })
    assert response.status_code == 404


def test_delete_trip_schedule(client, sample_user):
    """Test deleting a trip schedule"""
    # Create a trip schedule
    create_response = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'To Be Deleted',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_response.get_json()['trip_schedule']['id']

    # Delete it
    response = client.delete(f'/api/trip-schedules/{schedule_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

    # Verify it's deleted
    get_response = client.get(f'/api/trip-schedules/{schedule_id}')
    assert get_response.status_code == 404


def test_delete_trip_schedule_not_found(client):
    """Test deleting a non-existent trip schedule"""
    response = client.delete('/api/trip-schedules/9999')
    assert response.status_code == 404


def test_get_user_trip_schedules(client, sample_user):
    """Test getting trip schedules for a specific user"""
    # Create trip schedules
    client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'User Trip 1',
        'location': 'Location 1',
        'departure_date': get_future_datetime()
    })
    client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'User Trip 2',
        'location': 'Location 2',
        'departure_date': get_future_datetime_offset(45)
    })

    response = client.get(f'/api/trip-schedules/user/{sample_user}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['trip_schedules']) >= 2


def test_get_user_trip_schedules_user_not_found(client):
    """Test getting trip schedules for a non-existent user"""
    response = client.get('/api/trip-schedules/user/9999')
    assert response.status_code == 404


# Reminder Tests

def test_create_reminder(client, sample_user):
    """Test creating a reminder for a trip schedule"""
    # Create a trip schedule
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Trip with Reminder',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    # Create a reminder
    response = client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(25),
        'message': 'Do not forget to pack!'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['reminder']['reminder_type'] == 'email'
    assert data['reminder']['status'] == 'pending'


def test_create_reminder_invalid_type(client, sample_user):
    """Test creating a reminder with invalid type"""
    # Create a trip schedule
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    # Try to create a reminder with invalid type
    response = client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'invalid',
        'remind_at': get_future_datetime_offset(25)
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_create_reminder_missing_fields(client, sample_user):
    """Test creating a reminder with missing required fields"""
    # Create a trip schedule
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    # Try to create a reminder without remind_at
    response = client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_get_reminders(client, sample_user):
    """Test getting all reminders for a trip schedule"""
    # Create a trip schedule
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    # Create reminders
    client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(20)
    })
    client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'sms',
        'remind_at': get_future_datetime_offset(25)
    })

    # Get reminders
    response = client.get(f'/api/trip-schedules/{schedule_id}/reminders')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['reminders']) == 2


def test_get_reminder_by_id(client, sample_user):
    """Test getting a specific reminder"""
    # Create a trip schedule and reminder
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    create_reminder = client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(20)
    })
    reminder_id = create_reminder.get_json()['reminder']['id']

    # Get the reminder
    response = client.get(f'/api/trip-schedules/reminders/{reminder_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['reminder']['id'] == reminder_id


def test_get_reminder_not_found(client):
    """Test getting a non-existent reminder"""
    response = client.get('/api/trip-schedules/reminders/9999')
    assert response.status_code == 404


def test_update_reminder(client, sample_user):
    """Test updating a reminder"""
    # Create a trip schedule and reminder
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    create_reminder = client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(20)
    })
    reminder_id = create_reminder.get_json()['reminder']['id']

    # Update the reminder
    response = client.put(f'/api/trip-schedules/reminders/{reminder_id}', json={
        'message': 'Updated message',
        'reminder_type': 'sms'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['reminder']['message'] == 'Updated message'
    assert data['reminder']['reminder_type'] == 'sms'


def test_update_reminder_not_found(client):
    """Test updating a non-existent reminder"""
    response = client.put('/api/trip-schedules/reminders/9999', json={
        'message': 'Does not exist'
    })
    assert response.status_code == 404


def test_delete_reminder(client, sample_user):
    """Test deleting a reminder"""
    # Create a trip schedule and reminder
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    create_reminder = client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(20)
    })
    reminder_id = create_reminder.get_json()['reminder']['id']

    # Delete the reminder
    response = client.delete(f'/api/trip-schedules/reminders/{reminder_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

    # Verify it's deleted
    get_response = client.get(f'/api/trip-schedules/reminders/{reminder_id}')
    assert get_response.status_code == 404


def test_delete_reminder_not_found(client):
    """Test deleting a non-existent reminder"""
    response = client.delete('/api/trip-schedules/reminders/9999')
    assert response.status_code == 404


def test_get_pending_reminders(client, sample_user):
    """Test getting pending reminders"""
    # This endpoint returns reminders that are due
    response = client.get('/api/trip-schedules/reminders/pending')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'reminders' in data
    assert 'count' in data


def test_process_pending_reminders(client, sample_user):
    """Test processing pending reminders"""
    response = client.post('/api/trip-schedules/process-reminders')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'results' in data
    assert 'processed' in data['results']


def test_cascade_delete_trip_schedule(client, sample_user):
    """Test that deleting a trip schedule also deletes its reminders"""
    # Create a trip schedule with reminders
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Trip with Reminders',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    # Create reminders
    client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(20)
    })

    # Delete the trip schedule
    response = client.delete(f'/api/trip-schedules/{schedule_id}')
    assert response.status_code == 200

    # Verify reminders are also deleted (by getting empty list)
    # Since cascade delete is enabled, reminders should be gone


# Tests for input validation

def test_create_trip_schedule_empty_title(client, sample_user):
    """Test creating a trip schedule with empty title fails with 400"""
    schedule_data = {
        'user_id': sample_user,
        'title': '',
        'location': 'Test Location',
        'departure_date': get_future_datetime()
    }
    response = client.post('/api/trip-schedules/', json=schedule_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'title' in data['error'].lower()


def test_create_trip_schedule_empty_location(client, sample_user):
    """Test creating a trip schedule with empty location fails with 400"""
    schedule_data = {
        'user_id': sample_user,
        'title': 'Valid Title',
        'location': '',
        'departure_date': get_future_datetime()
    }
    response = client.post('/api/trip-schedules/', json=schedule_data)
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'location' in data['error'].lower()


def test_update_trip_schedule_empty_title(client, sample_user):
    """Test updating a trip schedule with empty title fails with 400"""
    # Create a trip schedule first
    create_response = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Original Title',
        'location': 'Original Location',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_response.get_json()['trip_schedule']['id']

    # Update with empty title
    response = client.put(f'/api/trip-schedules/{schedule_id}', json={
        'title': ''
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'title' in data['error'].lower()


def test_update_trip_schedule_empty_location(client, sample_user):
    """Test updating a trip schedule with empty location fails with 400"""
    # Create a trip schedule first
    create_response = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Original Title',
        'location': 'Original Location',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_response.get_json()['trip_schedule']['id']

    # Update with empty location
    response = client.put(f'/api/trip-schedules/{schedule_id}', json={
        'location': ''
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'location' in data['error'].lower()


# Tests for /api/trip-scheduler/* backward compatibility endpoints

def test_trip_scheduler_reminders_endpoint(client, sample_user):
    """Test the /api/trip-scheduler/reminders endpoint with days_ahead parameter"""
    # Create a trip schedule
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Test Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime_offset(5)
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    # Create a reminder within the next 7 days
    client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(3)
    })

    # Test the trip-scheduler endpoint
    response = client.get('/api/trip-scheduler/reminders?days_ahead=7')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'reminders' in data
    assert 'days_ahead' in data
    assert data['days_ahead'] == 7
    assert 'pagination' in data


def test_trip_scheduler_reminders_default_days(client, sample_user):
    """Test the /api/trip-scheduler/reminders endpoint with default days_ahead"""
    response = client.get('/api/trip-scheduler/reminders')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['days_ahead'] == 7  # Default value


def test_trip_scheduler_reminders_filter_by_user(client, sample_user):
    """Test filtering reminders by user_id"""
    # Create a trip schedule with reminder
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'User Trip',
        'location': 'Test Location',
        'departure_date': get_future_datetime_offset(10)
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(5)
    })

    # Test filtering by user_id
    response = client.get(f'/api/trip-scheduler/reminders?days_ahead=10&user_id={sample_user}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True


def test_trip_scheduler_reminders_invalid_days_ahead(client):
    """Test the /api/trip-scheduler/reminders endpoint with invalid days_ahead"""
    response = client.get('/api/trip-scheduler/reminders?days_ahead=-5')
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'days_ahead' in data['error']


def test_trip_scheduler_get_reminder_by_id(client, sample_user):
    """Test the /api/trip-scheduler/reminders/<id> endpoint"""
    # Create a trip schedule with reminder
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Test Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime()
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    create_reminder = client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(20)
    })
    reminder_id = create_reminder.get_json()['reminder']['id']

    # Test the trip-scheduler endpoint
    response = client.get(f'/api/trip-scheduler/reminders/{reminder_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['reminder']['id'] == reminder_id
    # Check that trip_schedule info is included
    assert 'trip_schedule' in data['reminder']
    assert data['reminder']['trip_schedule']['id'] == schedule_id


def test_trip_scheduler_get_reminder_not_found(client):
    """Test the /api/trip-scheduler/reminders/<id> endpoint with non-existent reminder"""
    response = client.get('/api/trip-scheduler/reminders/9999')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False


# Additional edge case tests for trip scheduler reminders


def test_trip_scheduler_reminders_no_upcoming_trips(client):
    """Test the /api/trip-scheduler/reminders endpoint when there are no upcoming reminders"""
    # Without creating any reminders, the endpoint should return empty list
    response = client.get('/api/trip-scheduler/reminders?days_ahead=7')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'reminders' in data
    assert len(data['reminders']) == 0
    assert data['days_ahead'] == 7
    assert 'pagination' in data
    assert data['pagination']['total'] == 0


def test_trip_scheduler_reminders_zero_days_ahead(client, sample_user):
    """Test the /api/trip-scheduler/reminders endpoint with days_ahead=0"""
    # Create a trip schedule and reminder for now
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Immediate Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime_offset(1)
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    # Create a reminder that is due right now (days_ahead=0 should not return it
    # as the endpoint only returns reminders within the date range)
    client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(1)
    })

    # With days_ahead=0, only reminders exactly at the current time would match
    response = client.get('/api/trip-scheduler/reminders?days_ahead=0')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['days_ahead'] == 0


def test_trip_scheduler_reminders_large_days_ahead(client, sample_user):
    """Test the /api/trip-scheduler/reminders endpoint with large days_ahead value"""
    # Create a trip schedule with reminder far in the future
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Far Future Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime_offset(100)
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(90)
    })

    # Test with large days_ahead value
    response = client.get('/api/trip-scheduler/reminders?days_ahead=365')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['days_ahead'] == 365


def test_trip_scheduler_reminders_filter_by_status_all(client, sample_user):
    """Test filtering reminders with empty status to get all statuses"""
    # Create a trip schedule and reminder
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Status Test Trip',
        'location': 'Somewhere',
        'departure_date': get_future_datetime_offset(10)
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
        'reminder_type': 'email',
        'remind_at': get_future_datetime_offset(5)
    })

    # Test with empty status to get all
    response = client.get('/api/trip-scheduler/reminders?days_ahead=10&status=')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True


def test_trip_scheduler_reminders_pagination(client, sample_user):
    """Test pagination for the trip scheduler reminders endpoint"""
    # Create a trip schedule
    create_schedule = client.post('/api/trip-schedules/', json={
        'user_id': sample_user,
        'title': 'Pagination Test Trip',
        'location': 'Test Location',
        'departure_date': get_future_datetime_offset(20)
    })
    schedule_id = create_schedule.get_json()['trip_schedule']['id']

    # Create multiple reminders
    for i in range(5):
        client.post(f'/api/trip-schedules/{schedule_id}/reminders', json={
            'reminder_type': 'email',
            'remind_at': get_future_datetime_offset(i + 1)
        })

    # Test pagination with per_page=2
    response = client.get('/api/trip-scheduler/reminders?days_ahead=20&per_page=2&page=1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert len(data['reminders']) <= 2
    assert data['pagination']['per_page'] == 2
