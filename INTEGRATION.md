# Integration Guide: Twende Tours Unified System

This guide explains how to integrate the `twende-backend`, `frontend`, and `daraja` repositories into a single cohesive system.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Integration Options](#integration-options)
4. [Integrated Deployment Setup](#integrated-deployment-setup)
5. [Database Configuration](#database-configuration)
6. [API Compatibility](#api-compatibility)
7. [Environment Variables](#environment-variables)
8. [Testing the Integration](#testing-the-integration)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)

## Overview

The Twende Tours system consists of three main components:

| Component | Purpose | Repository |
|-----------|---------|------------|
| **Backend** | REST API, database, business logic | `twende-backend` |
| **Frontend** | User interface (React/Vue/etc.) | `twende-frontend` or `frontend` |
| **Daraja** | M-Pesa payment pages | `daraja` |

### Architecture Options

```
Option 1: Integrated (Recommended)          Option 2: Separate
┌─────────────────────────────────┐         ┌─────────────────┐
│         twende-backend          │         │    Frontend     │
│  ┌───────────────────────────┐  │         │  (Netlify/etc)  │
│  │    Flask API Server       │  │         └────────┬────────┘
│  │    - /api/* endpoints     │  │                  │ CORS
│  │    - /health              │  │                  ▼
│  └───────────────────────────┘  │         ┌─────────────────┐
│  ┌───────────────────────────┐  │         │  twende-backend │
│  │    Static File Server     │  │         │    Flask API    │
│  │    - / serves frontend    │  │         └────────┬────────┘
│  │    - /daraja/* pages      │  │                  │
│  └───────────────────────────┘  │                  ▼
│  ┌───────────────────────────┐  │         ┌─────────────────┐
│  │      PostgreSQL DB        │◄─┼─────────│   PostgreSQL    │
│  └───────────────────────────┘  │         └─────────────────┘
└─────────────────────────────────┘
```

## Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend build)
- PostgreSQL 13+
- Git

## Integration Options

### Option 1: Integrated Deployment (Recommended)

All components run on the same server:
- ✅ No CORS issues
- ✅ Single deployment
- ✅ Simplified configuration
- ✅ Better performance

### Option 2: Separate Deployment

Frontend hosted separately:
- ⚠️ Requires CORS configuration
- ⚠️ Multiple deployments to manage
- ✅ Better for CDN-based frontend hosting

## Integrated Deployment Setup

### Step 1: Clone Repositories

```bash
# Clone all repositories in the same parent directory
git clone https://github.com/whco27/twende-backend.git
git clone https://github.com/whco27/twende-frontend.git  # or your frontend repo
git clone https://github.com/whco27/daraja.git  # if separate
```

### Step 2: Set Up Backend

```bash
cd twende-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (see Environment Variables section)
```

### Step 3: Deploy Frontend (Automated)

Use the provided deployment script:

```bash
# Make script executable (first time only)
chmod +x scripts/deploy_frontend.sh

# Deploy frontend
./scripts/deploy_frontend.sh ../twende-frontend
```

The script will:
1. Build the frontend with `npm run build`
2. Copy build artifacts to `public/` directory
3. Verify the deployment

### Step 3 (Alternative): Deploy Frontend (Manual)

```bash
# Build frontend
cd ../twende-frontend
npm install
npm run build

# Copy to backend
cp -r dist/* ../twende-backend/public/
# Or for Create React App: cp -r build/* ../twende-backend/public/
```

### Step 4: Deploy Daraja Pages

If you have separate Daraja HTML pages:

```bash
# Copy Daraja static files
cp -r ../daraja/* twende-backend/public/daraja/

# Or if Daraja is part of frontend build, it's already included
```

A sample payment page is provided at `public/daraja/payment.html`.

### Step 5: Configure for Integrated Mode

Update `.env`:

```bash
# Disable CORS for same-origin requests
ENABLE_CORS=false
```

### Step 6: Start the Server

```bash
cd twende-backend
python app.py
```

Access the application:
- Frontend: http://localhost:5000/
- API: http://localhost:5000/api/
- Daraja Payment: http://localhost:5000/daraja/payment.html
- Health Check: http://localhost:5000/health

## Database Configuration

### Single Database for All Components

All components share the same PostgreSQL database. Configure in `.env`:

```bash
DATABASE_URL=postgresql://username:password@host:5432/twende_tours
```

### Database Schema

The backend automatically creates these tables:

```
┌─────────────────┐     ┌─────────────────┐
│     users       │     │     tours       │
├─────────────────┤     ├─────────────────┤
│ id              │     │ id              │
│ email           │     │ title           │
│ password_hash   │     │ description     │
│ first_name      │     │ price           │
│ last_name       │     │ duration        │
│ phone_number    │     │ location        │
│ created_at      │     │ image_url       │
│ is_active       │     │ available_slots │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────┴──────┐
              │  bookings   │
              ├─────────────┤
              │ id          │
              │ user_id  ──►│
              │ tour_id  ──►│
              │ tour_date   │
              │ total_amount│
              │ status      │
              │ payment_ref │
              └──────┬──────┘
                     │
              ┌──────┴──────┐
              │  payments   │
              ├─────────────┤
              │ id          │
              │ booking_id  │
              │ checkout_id │
              │ amount      │
              │ status      │
              │ mpesa_receipt│
              └─────────────┘
```

### Initialize Database

Tables are created automatically when the app starts:

```python
# In app.py (already configured)
with app.app_context():
    db.create_all()
```

### Migrations (Optional)

For production, consider using Flask-Migrate:

```bash
pip install Flask-Migrate

# Initialize migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## API Compatibility

### Frontend API Integration

Update your frontend API calls to use relative URLs:

```javascript
// Before (separate deployment)
const API_BASE = 'https://api.example.com';
fetch(`${API_BASE}/api/tours/`);

// After (integrated deployment)
const API_BASE = '';  // Empty for same-origin
fetch(`/api/tours/`);
```

### Available API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tours/` | GET | List all tours |
| `/api/tours/<id>` | GET | Get tour details |
| `/api/tours/` | POST | Create tour |
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/auth/check-email` | POST | Check email availability |
| `/api/bookings/` | GET/POST | List/create bookings |
| `/api/bookings/<id>` | GET/PUT | Get/update booking |
| `/api/bookings/<id>/cancel` | POST | Cancel booking |
| `/api/payments/initiate` | POST | Start M-Pesa payment |
| `/api/payments/status/<id>` | GET | Check payment status |
| `/api/payments/callback` | POST | M-Pesa webhook |
| `/health` | GET | Health check |

### Daraja API Integration

The Daraja payment flow:

```javascript
// 1. Create booking first
const booking = await fetch('/api/bookings/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        user_id: userId,
        tour_id: tourId,
        tour_date: '2024-03-15',
        number_of_guests: 2
    })
}).then(r => r.json());

// 2. Initiate M-Pesa payment
const payment = await fetch('/api/payments/initiate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        booking_id: booking.booking.id,
        phone_number: '0712345678'
    })
}).then(r => r.json());

// 3. Poll for payment status
const checkStatus = async (checkoutId) => {
    const status = await fetch(`/api/payments/status/${checkoutId}`)
        .then(r => r.json());
    return status.payment.status;
};
```

## Environment Variables

### Complete Configuration

```bash
# ============ Core Settings ============
FLASK_ENV=production
SECRET_KEY=your-secure-random-key
DATABASE_URL=postgresql://user:pass@host:5432/twende_tours

# ============ Integration Mode ============
# Set false for integrated deployment
ENABLE_CORS=false

# ============ Email Notifications ============
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@twendetours.com
ADMIN_EMAILS=admin@example.com

# ============ Daraja (M-Pesa) ============
DARAJA_ENV=production  # or 'sandbox' for testing
DARAJA_CONSUMER_KEY=your_consumer_key
DARAJA_CONSUMER_SECRET=your_consumer_secret
DARAJA_PASSKEY=your_passkey
DARAJA_SHORTCODE=your_shortcode
DARAJA_CALLBACK_URL=https://your-domain.com/api/payments/callback
```

## Testing the Integration

### 1. Start the Backend

```bash
cd twende-backend
source venv/bin/activate
python app.py
```

### 2. Run Automated Tests

```bash
python -m pytest tests/ -v
```

### 3. Test API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Get tours
curl http://localhost:5000/api/tours/

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","first_name":"Test","last_name":"User"}'
```

### 4. Test Frontend Integration

1. Open http://localhost:5000/ in browser
2. Navigate through the application
3. Verify API calls work without CORS errors

### 5. Test Daraja Payment

1. Open http://localhost:5000/daraja/payment.html
2. Enter a valid booking ID
3. Enter an M-Pesa test phone number
4. Verify STK push is initiated

## Production Deployment

### Railway

```bash
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn app:app"
```

Environment variables in Railway dashboard:
- `DATABASE_URL` (auto-provided with PostgreSQL add-on)
- `ENABLE_CORS=false`
- All Daraja credentials

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY . .

# Copy pre-built frontend (build before Docker build)
# COPY --from=frontend-builder /app/dist ./public/

EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

### Render

Build command:
```bash
pip install -r requirements.txt
```

Start command:
```bash
gunicorn app:app
```

## Troubleshooting

### CORS Errors

**Problem**: Browser shows CORS errors.

**Solution**: 
- For integrated deployment: Set `ENABLE_CORS=false`
- For separate deployment: Add frontend URL to `FRONTEND_URL`

### 404 on Frontend Routes

**Problem**: Direct access to `/tours` returns 404.

**Solution**: Ensure `index.html` exists in `public/`. The backend serves it for all non-API routes (SPA routing).

### Database Connection Failed

**Problem**: "Connection refused" errors.

**Solution**:
1. Verify PostgreSQL is running
2. Check `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
3. Ensure database exists

### M-Pesa STK Not Received

**Problem**: No prompt on phone after payment initiation.

**Solution**:
1. Verify Daraja credentials are correct
2. Ensure `DARAJA_ENV` matches credentials (sandbox vs production)
3. Check phone number format (should be 254XXXXXXXXX)
4. Verify callback URL is publicly accessible

### Frontend Not Loading

**Problem**: Root URL shows API info instead of frontend.

**Solution**:
1. Run `./scripts/deploy_frontend.sh` to deploy frontend
2. Verify `public/index.html` exists
3. Check frontend build succeeded

## Support

For issues:
1. Check logs: `python app.py` shows Flask logs
2. Run tests: `pytest tests/ -v`
3. Check health: `curl localhost:5000/health`
