# Twende Tours Backend API

A Flask-based REST API backend for the Twende Tours application, providing tour management, user authentication, booking management, and M-Pesa Daraja payment integration.

## 🚀 Quick Start (Integrated Deployment)

For the fastest setup with frontend served from the same server:

```bash
# 1. Clone and setup
git clone https://github.com/whco27/twende-backend.git
cd twende-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your DATABASE_URL and other settings
# Set ENABLE_CORS=false for integrated deployment

# 3. Deploy frontend (optional - if you have a frontend repo)
./scripts/deploy_frontend.sh ../twende-frontend

# 4. Run
python app.py
# Access at http://localhost:5000
```

📖 **For detailed integration instructions, see [INTEGRATION.md](INTEGRATION.md)**

## Features

- **Tour Management**: CRUD operations for tour listings
- **User Authentication**: User registration and login with email notifications
- **Booking System**: Tour booking with slot management
- **M-Pesa Integration**: Daraja API integration for STK Push payments
- **Email Notifications**: Registration confirmation emails and admin notifications for new users
- **Health Monitoring**: Health check endpoint with database status
- **CORS Support**: Configurable CORS for frontend integration
- **Integrated Frontend Hosting**: Serve frontend and Daraja static files from the same server
- **Unified Database**: Single PostgreSQL database for all components

## API Endpoints

### Base URL
- Development: `http://localhost:5000`
- Production: Your deployed URL

### Tours API (`/api/tours`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tours/` | Get all tours |
| GET | `/api/tours/<id>` | Get tour by ID |
| POST | `/api/tours/` | Create a new tour |
| PUT | `/api/tours/<id>` | Update a tour |
| DELETE | `/api/tours/<id>` | Delete a tour |

### Authentication API (`/api/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login user |
| POST | `/api/auth/check-email` | Check email availability |
| GET | `/api/auth/user/<id>` | Get user by ID |
| PUT | `/api/auth/user/<id>` | Update user |

#### User Registration

**POST** `/api/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "0712345678"  // optional
}
```

**Validation Rules:**
- `email`: Required, valid email format, max 255 characters, must be unique
- `password`: Required, minimum 8 characters
- `first_name`: Required, max 100 characters
- `last_name`: Required, max 100 characters
- `phone_number`: Optional, max 20 characters

**Note:** All string inputs are automatically trimmed of leading/trailing whitespace.

**Error Responses:**
- `400 Bad Request`: Validation errors (missing fields, invalid format, field too long)
- `409 Conflict`: Email is already registered. Returns `{"success": false, "error": "User with this email already exists"}` or `{"success": false, "error": "Email is already in use"}` for race condition handling.
- `500 Internal Server Error`: Server error during registration

#### Check Email Availability

**POST** `/api/auth/check-email`

Pre-validate email availability before registration. Use this endpoint to provide immediate feedback to users.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "available": true,
  "message": "Email is available"
}
```

Or if email is taken:
```json
{
  "success": true,
  "available": false,
  "message": "Email is already in use"
}
```

**Error Response (400):**
```json
{
  "success": false,
  "error": "Invalid email format",
  "available": false
}
```

### Bookings API (`/api/bookings`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/bookings/` | Get all bookings (filter by user_id, status) |
| GET | `/api/bookings/<id>` | Get booking by ID |
| POST | `/api/bookings/` | Create a new booking |
| PUT | `/api/bookings/<id>` | Update booking |
| POST | `/api/bookings/<id>/cancel` | Cancel a booking |
| GET | `/api/bookings/user/<user_id>` | Get user's bookings |

### Payments API (`/api/payments`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/initiate` | Initiate M-Pesa STK Push payment |
| POST | `/api/payments/callback` | M-Pesa callback URL (webhook) |
| GET | `/api/payments/status/<checkout_request_id>` | Check payment status |
| GET | `/api/payments/booking/<booking_id>` | Get payments for a booking |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and available endpoints |
| GET | `/health` | Health check with database status |

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL (for production)
- M-Pesa Daraja API credentials (for payments)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/whco27/twende-backend.git
cd twende-backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
python app.py
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `FLASK_ENV` | Environment (development/production) | No |
| `ENABLE_CORS` | Enable CORS for external frontend (default: true) | No |
| `FRONTEND_URL` | Allowed frontend origins (comma-separated) | No |
| `MAIL_SERVER` | SMTP server hostname | For email notifications |
| `MAIL_PORT` | SMTP port (default: 587) | For email notifications |
| `MAIL_USE_TLS` | Use TLS (default: true) | For email notifications |
| `MAIL_USE_SSL` | Use SSL (default: false) | For email notifications |
| `MAIL_USERNAME` | SMTP username/email | For email notifications |
| `MAIL_PASSWORD` | SMTP password/app password | For email notifications |
| `MAIL_DEFAULT_SENDER` | Default sender email | For email notifications |
| `ADMIN_EMAILS` | Admin emails for notifications (comma-separated) | For admin notifications |
| `DARAJA_CONSUMER_KEY` | Safaricom Daraja consumer key | For payments |
| `DARAJA_CONSUMER_SECRET` | Safaricom Daraja consumer secret | For payments |
| `DARAJA_PASSKEY` | Safaricom Daraja passkey | For payments |
| `DARAJA_SHORTCODE` | M-Pesa business shortcode | For payments |
| `DARAJA_CALLBACK_URL` | Payment callback URL | For payments |
| `DARAJA_ENV` | Daraja environment (sandbox/production) | For payments |

## Integration Guide

### Frontend Integration

The backend supports two modes for frontend integration:

#### Option 1: Integrated Deployment (Recommended)

Host the frontend and backend on the same server to eliminate CORS issues and simplify deployment.

**Steps to integrate frontend:**

1. **Build the frontend** (in your frontend repository):
   ```bash
   cd twende-frontend
   npm install
   npm run build
   ```

2. **Copy build artifacts** to the backend's `public/` directory:
   ```bash
   cp -r build/* ../twende-backend/public/
   # Or for Vite-based projects:
   cp -r dist/* ../twende-backend/public/
   ```

3. **Configure environment** to disable CORS:
   ```bash
   ENABLE_CORS=false
   ```

4. **Deploy** the backend with the frontend assets included.

**How it works:**
- Static files (JS, CSS, images) are served from the `public/` directory
- The root URL (`/`) serves `index.html` when the frontend is deployed
- All non-API routes (e.g., `/tours`, `/about`) serve `index.html` for client-side routing (SPA)
- API routes (`/api/*`) continue to work normally and return JSON

**Directory structure after integration:**
```
twende-backend/
├── app.py
├── public/
│   ├── index.html       # Frontend entry point
│   ├── assets/          # JS, CSS bundles
│   └── ...              # Other static files
├── routes/
└── ...
```

#### Option 2: Separate Deployment (External Frontend)

Host the frontend on a separate server (e.g., Netlify, Vercel, or another hosting service).

**Configuration:**
```bash
ENABLE_CORS=true
FRONTEND_URL=https://your-frontend-domain.com
```

**Example frontend fetch:**
```javascript
// Get all tours
const response = await fetch('http://localhost:5000/api/tours/');
const tours = await response.json();

// User login
const loginResponse = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', password: 'password123' })
});
const { success, user } = await loginResponse.json();
```

### Email Notifications Setup

The backend supports email notifications for:
- **User Registration Confirmation**: Welcome email sent to users after successful registration
- **Admin Notifications**: Alerts admins when new users register

**Gmail Setup Example:**
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password at https://myaccount.google.com/apppasswords
3. Configure environment variables:
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=noreply@twendetours.com
ADMIN_EMAILS=admin1@example.com,admin2@example.com
```

**Note:** Email notifications are optional. If not configured, registration will still succeed without sending emails.

### Daraja (M-Pesa) Integration

1. Register at [Safaricom Daraja Portal](https://developer.safaricom.co.ke/)
2. Create an app to get consumer key and secret
3. Get the passkey for STK Push
4. Configure callback URL for payment notifications

**Payment Flow:**
1. Frontend creates a booking via `/api/bookings/`
2. Frontend initiates payment via `/api/payments/initiate` with `booking_id` and `phone_number`
3. User receives STK Push prompt on their phone
4. M-Pesa sends callback to `/api/payments/callback`
5. Frontend polls `/api/payments/status/<checkout_request_id>` for payment status

### Database Schema

The application uses the following models:
- **Tour**: Tour listings with title, description, price, duration, location
- **User**: User accounts with email, password, profile info
- **Booking**: Tour reservations linking users to tours
- **Payment**: M-Pesa payment records linked to bookings

## Testing

Run tests with pytest:
```bash
python -m pytest tests/ -v
```

Run with coverage:
```bash
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

## Deployment

### Integrated Deployment (Frontend + Backend)

For integrated deployment with the frontend served from the same server:

1. **Build frontend** in your frontend repository:
   ```bash
   npm run build
   ```

2. **Copy frontend build** to `public/` directory:
   ```bash
   cp -r dist/* public/
   # Or for Create React App:
   cp -r build/* public/
   ```

3. **Set environment variables**:
   ```bash
   ENABLE_CORS=false  # Disable CORS since frontend is on same origin
   ```

4. **Deploy** using your preferred platform (Railway, Render, Docker).

### Railway

Railway is the recommended deployment platform for Twende Tours. Here's a complete setup guide:

**Step 1: Create Project**
1. Create a new project on Railway
2. Click **"Deploy from GitHub repo"**
3. Select the `twende-backend` repository

**Step 2: Add PostgreSQL**
1. In your project, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway automatically sets `DATABASE_URL` for your backend

**Step 3: Configure Environment Variables**

Required variables in Railway dashboard:
```bash
SECRET_KEY=your-secure-random-key
FLASK_ENV=production
ENABLE_CORS=true  # Set to false if frontend served from same origin
FRONTEND_URL=https://your-frontend.netlify.app  # Your frontend's URL
```

**Step 4: Verify Deployment**
```bash
# Check health endpoint
curl https://your-app.up.railway.app/health

# Expected response:
# {"status": "healthy", "database": "healthy", "service": "twende-backend"}
```

**Step 5: Connect Frontend**

In your frontend `.env` file:
```bash
REACT_APP_API_URL=https://your-app.up.railway.app
# or for Vue/Vite:
VITE_API_URL=https://your-app.up.railway.app
```

📖 **For detailed Railway deployment, see [INTEGRATION.md](INTEGRATION.md#railway-deployment-guide)**

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD gunicorn app:app --bind 0.0.0.0:$PORT
```

**For integrated frontend deployment**, ensure the `public/` directory contains the built frontend files before building the Docker image.

### Render

1. Connect repository to Render
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn app:app`
4. Configure environment variables

## API Response Format

All API responses follow a consistent format:

**Success:**
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Project Structure

```
twende-backend/
├── app.py                    # Main Flask application
├── config.py                 # Configuration classes
├── requirements.txt          # Python dependencies
├── Procfile                  # Deployment configuration
├── INTEGRATION.md           # Detailed integration guide
├── .env.example              # Environment variable template
├── models/                   # Database models
│   ├── __init__.py
│   ├── tour.py              # Tour model
│   ├── user.py              # User model
│   ├── booking.py           # Booking model
│   └── payment.py           # Payment model
├── routes/                   # API route handlers
│   ├── __init__.py          # Tours routes
│   ├── auth.py              # Authentication routes
│   ├── bookings.py          # Booking routes
│   └── payments.py          # Daraja payment routes
├── services/                 # Business logic services
│   ├── __init__.py
│   └── notifications.py     # Email notification service
├── public/                   # Frontend static files
│   ├── .gitkeep
│   └── daraja/              # Daraja payment pages
│       ├── README.md
│       └── payment.html     # Sample M-Pesa payment page
├── scripts/                  # Utility scripts
│   └── deploy_frontend.sh   # Frontend deployment script
└── tests/                    # Test suite
    ├── conftest.py
    ├── test_auth.py
    ├── test_bookings.py
    ├── test_frontend_serving.py
    ├── test_notifications.py
    ├── test_payments.py
    └── test_tours.py
```

## Related Repositories

| Repository | Description |
|------------|-------------|
| `twende-backend` | This repository - REST API backend |
| `twende-frontend` | React/Vue frontend application |
| `daraja` | M-Pesa Daraja payment integration pages |

All repositories are designed to work together. See [INTEGRATION.md](INTEGRATION.md) for setup instructions.

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Submit a pull request
