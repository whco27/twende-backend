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
8. [Frontend Environment Setup](#frontend-environment-setup)
9. [Testing the Integration](#testing-the-integration)
10. [Production Deployment](#production-deployment)
11. [Railway Deployment Guide](#railway-deployment-guide)
12. [End-to-End Testing Guide](#end-to-end-testing-guide)
13. [Troubleshooting](#troubleshooting)

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
| `/api/tours/` | GET | List all tours (supports `page`, `per_page`, `location` params) |
| `/api/tours/<id>` | GET | Get tour details |
| `/api/tours/` | POST | Create tour |
| `/api/tours/search` | GET | Search tours (supports `title`, `location`, `min_price`, `max_price`, `page`, `per_page` params) |
| `/api/tours/seed` | POST | Seed database with default tours (30+ Kenyan tours) |
| `/api/tours/bulk-import` | POST | Bulk import tours from frontend data |
| `/api/tours/by-title/<title>` | GET | Get tour by exact title |
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/auth/check-email` | POST | Check email availability |
| `/api/auth/users` | GET | List all users (supports `page`, `per_page`, `is_active` params) |
| `/api/bookings/` | GET/POST | List/create bookings (supports `page`, `per_page`, `user_id`, `status` params) |
| `/api/bookings/<id>` | GET/PUT/DELETE | Get/update/delete booking |
| `/api/bookings/<id>/cancel` | POST | Cancel booking |
| `/api/bookings/user/<user_id>` | GET | Get user's bookings (supports `page`, `per_page` params) |
| `/api/payments/` | GET | List all payments (supports `status`, `booking_id`, `page`, `per_page` params) |
| `/api/payments/initiate` | POST | Start M-Pesa payment |
| `/api/payments/status/<id>` | GET | Check payment status |
| `/api/payments/callback` | POST | M-Pesa webhook |
| `/api/payments/booking/<id>` | GET | Get payments for a booking |
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

## Frontend Environment Setup

When setting up a separate frontend application (React, Vue, etc.) to connect to this backend, configure the following environment variables:

### React Applications

Create a `.env` file in your frontend project root:

```bash
# Backend API URL - use your Railway deployed backend URL
REACT_APP_API_URL=https://your-backend-app.up.railway.app

# For local development (when running backend locally)
# REACT_APP_API_URL=http://localhost:5000
```

### Vue.js Applications

Create a `.env` file:

```bash
# Vue 3 / Vite
VITE_API_URL=https://your-backend-app.up.railway.app

# Vue 2 / Vue CLI
VUE_APP_API_URL=https://your-backend-app.up.railway.app
```

### Using Environment Variables in Frontend Code

**React Example:**
```javascript
// src/config/api.js
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

export const apiClient = {
  async register(userData) {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  },
  
  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return response.json();
  },
  
  async getTours() {
    const response = await fetch(`${API_BASE_URL}/api/tours/`);
    return response.json();
  }
};
```

**Vue Example:**
```javascript
// src/services/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export default {
  async register(userData) {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  }
};
```

### Important Notes

1. **Never commit `.env` files** - Add `.env` to your `.gitignore`
2. **Use `.env.example`** - Create a template file for team members
3. **Trailing slashes** - API base URLs should NOT include trailing slashes to avoid double slashes when concatenating endpoints (e.g., use `https://api.example.com` not `https://api.example.com/`)
4. **CORS Configuration** - If frontend is on a different domain, set `ENABLE_CORS=true` and add frontend URL to `FRONTEND_URL` in backend

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
1. Check configuration status: `curl /api/payments/config/status`
2. Verify Daraja credentials are correct
3. Ensure `DARAJA_ENV` matches credentials (sandbox vs production)
4. Check phone number format (should be 254XXXXXXXXX for Kenyan mobile)
5. Verify callback URL is publicly accessible (HTTPS required for production)

### M-Pesa "Failed to fetch" Error

**Problem**: Frontend shows "Failed to fetch" when initiating payment.

**Solution**:
1. Check payment service health: `curl /api/payments/health`
2. Verify CORS is configured correctly (`ENABLE_CORS=true` and `FRONTEND_URL` set)
3. Check browser developer console for specific error details
4. Verify the backend server is running and accessible
5. Ensure API requests include proper `Content-Type: application/json` header

### M-Pesa Timeout Errors

**Problem**: Payment requests timeout.

**Solution**:
1. The system automatically retries failed requests up to 3 times
2. Check network connectivity to Safaricom's servers
3. Verify correct `DARAJA_ENV` setting (sandbox or production)
4. Check the payment service health endpoint for connectivity status

### Invalid Phone Number Error

**Problem**: Payment initiation fails with invalid phone number error.

**Solution**:
1. Use Kenyan mobile format: `07XXXXXXXX` or `254XXXXXXXXX`
2. Phone must be a valid Kenyan mobile number (starting with 07XX or 01XX)
3. Remove any spaces or special characters from the phone number

### Frontend Not Loading

**Problem**: Root URL shows API info instead of frontend.

**Solution**:
1. Run `./scripts/deploy_frontend.sh` to deploy frontend
2. Verify `public/index.html` exists
3. Check frontend build succeeded

## Payment API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/payments/initiate` | POST | Initiate STK Push payment |
| `/api/payments/callback` | POST | M-Pesa callback webhook |
| `/api/payments/status/<checkout_id>` | GET | Check payment status |
| `/api/payments/booking/<booking_id>` | GET | Get payments for a booking |
| `/api/payments/config/status` | GET | Check M-Pesa configuration |
| `/api/payments/health` | GET | Check payment service health |

### Error Codes

| Code | Description |
|------|-------------|
| `NO_DATA` | No JSON data provided in request |
| `MISSING_FIELDS` | Required fields are missing |
| `INVALID_BOOKING_ID` | Booking ID is not a valid integer |
| `BOOKING_NOT_FOUND` | Booking does not exist |
| `ALREADY_PAID` | Booking has already been paid |
| `INVALID_PHONE` | Phone number format is invalid |
| `SERVICE_NOT_CONFIGURED` | M-Pesa credentials not configured |
| `INVALID_AMOUNT` | Invalid booking amount |
| `AUTH_FAILED` | M-Pesa authentication failed |
| `TIMEOUT` | Request to M-Pesa timed out |
| `CONNECTION_ERROR` | Unable to connect to M-Pesa |
| `STK_PUSH_FAILED` | STK Push request failed |

## Support

For issues:
1. Check logs: `python app.py` shows Flask logs
2. Run tests: `pytest tests/ -v`
3. Check health: `curl localhost:5000/health`
4. Check payment health: `curl localhost:5000/api/payments/health`

## Railway Deployment Guide

This section provides detailed instructions for deploying the Twende Tours backend on Railway with PostgreSQL.

### Step 1: Create Railway Project

1. Sign up or log in to [Railway](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select the `twende-backend` repository
4. Railway will automatically detect the Python project

### Step 2: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Wait for the database to provision
4. Railway automatically sets `DATABASE_URL` for connected services

### Step 3: Configure Environment Variables

In the Railway dashboard, go to your backend service and add these variables:

**Required Variables:**
```bash
# Flask configuration
SECRET_KEY=your-random-secure-key-here
FLASK_ENV=production

# CORS - set to true if frontend is on different domain
ENABLE_CORS=true
FRONTEND_URL=https://your-frontend.netlify.app,https://your-frontend.vercel.app
```

**Optional - Email Notifications:**
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@twendetours.com
ADMIN_EMAILS=admin@twendetours.com
```

**Optional - M-Pesa Payments:**
```bash
DARAJA_ENV=production
DARAJA_CONSUMER_KEY=your_key
DARAJA_CONSUMER_SECRET=your_secret
DARAJA_PASSKEY=your_passkey
DARAJA_SHORTCODE=your_shortcode
DARAJA_CALLBACK_URL=https://your-backend.up.railway.app/api/payments/callback
```

### Step 4: Deploy and Verify

1. Railway deploys automatically when you push to the connected branch
2. Check the deployment logs for any errors
3. Once deployed, note your backend URL (e.g., `https://your-backend.up.railway.app`)

### Step 5: Verify Database Connectivity

Test the health endpoint:
```bash
curl https://your-backend.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "service": "twende-backend"
}
```

### Step 6: Verify Database Tables

The backend automatically creates tables on startup. You can verify by:
1. Connecting to Railway's PostgreSQL via the dashboard
2. Running: `SELECT * FROM information_schema.tables WHERE table_schema = 'public';`

Expected tables:
- `users`
- `tours`
- `bookings`
- `payments`

## End-to-End Testing Guide

This section provides a comprehensive guide for testing the user registration flow from frontend to backend to database.

### Prerequisites

- Backend deployed on Railway (or running locally)
- PostgreSQL database connected and healthy

### Test 1: Health Check

Verify backend is running and database is connected:

```bash
# Replace with your Railway URL or localhost:5000
BACKEND_URL="https://your-backend.up.railway.app"

curl $BACKEND_URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "service": "twende-backend"
}
```

### Test 2: User Registration

Test the complete registration flow:

```bash
# Test successful registration
curl -X POST "$BACKEND_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "securepass123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "0712345678"
  }'
```

**Expected Success Response (201):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "0712345678",
    "created_at": "2024-01-15T10:30:00.000000",
    "is_active": true
  }
}
```

### Test 3: Duplicate Email Handling

Verify duplicate email registration is handled:

```bash
# Try registering with the same email again
curl -X POST "$BACKEND_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "anotherpass123",
    "first_name": "Another",
    "last_name": "User"
  }'
```

**Expected Error Response (409):**
```json
{
  "success": false,
  "error": "User with this email already exists"
}
```

### Test 4: Email Availability Check

Pre-check email availability before registration:

```bash
# Check if email is available
curl -X POST "$BACKEND_URL/api/auth/check-email" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com"}'
```

**Expected Response (Available):**
```json
{
  "success": true,
  "available": true,
  "message": "Email is available"
}
```

**Expected Response (Taken):**
```json
{
  "success": true,
  "available": false,
  "message": "Email is already in use"
}
```

### Test 5: User Login

Verify the registered user can log in:

```bash
curl -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "securepass123"
  }'
```

**Expected Success Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "testuser@example.com",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "0712345678",
    "is_active": true
  }
}
```

### Test 6: Validation Error Handling

Test various validation scenarios:

```bash
# Missing required field
curl -X POST "$BACKEND_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "pass123"}'
# Expected: 400 - "Missing required field: first_name"

# Invalid email format
curl -X POST "$BACKEND_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email", "password": "pass12345", "first_name": "Test", "last_name": "User"}'
# Expected: 400 - "Invalid email format"

# Password too short
curl -X POST "$BACKEND_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test2@example.com", "password": "short", "first_name": "Test", "last_name": "User"}'
# Expected: 400 - "Password must be at least 8 characters long"
```

### Frontend Integration Test Script

Use this script to test from a frontend context:

```javascript
// test-registration.js - Run in browser console or Node.js

// Use environment variable if available, otherwise fallback to placeholder
const API_URL = (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_URL) 
  || 'https://your-backend.up.railway.app';  // Replace with your actual Railway URL

async function testRegistrationFlow() {
  console.log('Testing User Registration Flow...\n');
  
  // Generate unique email for test
  const testEmail = `test_${Date.now()}@example.com`;
  
  // Test 1: Check email availability
  console.log('1. Checking email availability...');
  const checkResponse = await fetch(`${API_URL}/api/auth/check-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: testEmail })
  });
  const checkData = await checkResponse.json();
  console.log('   Result:', checkData.available ? 'Email available ✓' : 'Email taken ✗');
  
  // Test 2: Register new user
  console.log('\n2. Registering new user...');
  const registerResponse = await fetch(`${API_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: testEmail,
      password: 'securepass123',
      first_name: 'Integration',
      last_name: 'Test',
      phone_number: '0712345678'
    })
  });
  const registerData = await registerResponse.json();
  console.log('   Result:', registerData.success ? 'Registration successful ✓' : `Failed: ${registerData.error}`);
  
  if (registerData.success) {
    console.log('   User ID:', registerData.user.id);
    console.log('   Email:', registerData.user.email);
  }
  
  // Test 3: Login with new user
  console.log('\n3. Logging in with new user...');
  const loginResponse = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: testEmail,
      password: 'securepass123'
    })
  });
  const loginData = await loginResponse.json();
  console.log('   Result:', loginData.success ? 'Login successful ✓' : `Failed: ${loginData.error}`);
  
  // Test 4: Duplicate registration
  console.log('\n4. Testing duplicate email handling...');
  const duplicateResponse = await fetch(`${API_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: testEmail,
      password: 'anotherpass123',
      first_name: 'Duplicate',
      last_name: 'Test'
    })
  });
  const duplicateData = await duplicateResponse.json();
  console.log('   Result:', duplicateData.success === false ? 'Duplicate rejected correctly ✓' : 'Error: duplicate was accepted ✗');
  
  console.log('\n=== Test Complete ===');
}

testRegistrationFlow().catch(console.error);
```

### Automated Test Suite

Run the backend's test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
python -m pytest tests/ -v

# Run only authentication tests
python -m pytest tests/test_auth.py -v

# Run with coverage report
python -m pytest tests/ --cov=. --cov-report=html
```

### Troubleshooting Test Failures

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Backend not running or wrong URL | Verify `BACKEND_URL` and backend is deployed |
| `CORS error` | Frontend domain not allowed | Add frontend URL to `FRONTEND_URL` env var |
| `Database unhealthy` | PostgreSQL connection issue | Check `DATABASE_URL` and database service status |
| `500 Internal Server Error` | Backend exception | Check Railway logs for stack trace |

### Cleaning Up Test Data

If you need to clean up test users from the database:

```sql
-- Connect to PostgreSQL and run:
DELETE FROM users WHERE email LIKE 'test%@example.com';
```

## Best Practices for Backend Data Storage

This section provides guidelines for ensuring data consistency between the frontend, Daraja API, and backend database.

### 1. Always Use Backend Database as Source of Truth

**DO NOT** rely on local storage for critical data like tours, bookings, or payments. Always:

- Fetch tour data from `/api/tours/` instead of storing locally
- Create bookings via `/api/bookings/` endpoint
- Track payment status via `/api/payments/status/<checkout_id>`

```javascript
// ❌ Bad: Storing tours in local storage
localStorage.setItem('selectedTour', JSON.stringify(tour));

// ✅ Good: Always fetch from backend
const tour = await fetch(`${API_URL}/api/tours/${tourId}`).then(r => r.json());
```

### 2. Seed Tours on Deployment

When deploying a new environment, seed the database with default tours (30+ Kenyan tours including safaris, beach getaways, and cultural experiences):

```bash
# Call the seed endpoint after deployment
curl -X POST https://your-backend.up.railway.app/api/tours/seed
```

Or programmatically during frontend initialization:

```javascript
// Check if tours exist, seed if empty
async function ensureToursExist() {
  const response = await fetch(`${API_URL}/api/tours/`);
  const tours = await response.json();
  
  if (tours.length === 0) {
    // Seed default tours
    await fetch(`${API_URL}/api/tours/seed`, { method: 'POST' });
  }
}
```

### 2.1 Bulk Import Tours from Frontend

If you have custom tour data in your frontend, you can bulk import it:

```javascript
// Bulk import tours from frontend data
async function bulkImportTours(toursData) {
  const response = await fetch(`${API_URL}/api/tours/bulk-import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tours: toursData,
      update_existing: false  // Set to true to update existing tours
    })
  });
  
  const result = await response.json();
  console.log(`Created: ${result.created_count}, Updated: ${result.updated_count}, Skipped: ${result.skipped_count}`);
  return result;
}

// Example usage with frontend tour data
const frontendTours = [
  {
    title: 'Custom Safari Tour',
    description: 'Your custom tour description',
    price: 50000.0,
    duration: '3 days',
    location: 'Custom Location',
    image_url: 'https://example.com/image.jpg',  // optional
    available_slots: 20  // optional, defaults to 10
  }
];

bulkImportTours(frontendTours);
```

### 3. Search Tours by Title

If you need to find a specific tour (e.g., "Masai Mara 3-Day Safari"):

```javascript
// Search for tour by title
const response = await fetch(
  `${API_URL}/api/tours/search?title=${encodeURIComponent('Masai Mara')}`
);
const data = await response.json();
const tour = data.tours[0];
```

### 4. Handle Tour Not Found Errors

When creating bookings, the API returns detailed error codes:

```javascript
const response = await fetch(`${API_URL}/api/bookings/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: userId,
    tour_id: tourId,
    tour_date: '2024-03-15',
    number_of_guests: 2
  })
});

const data = await response.json();

if (!data.success && data.error_code === 'TOUR_NOT_FOUND') {
  // Tour doesn't exist in database
  console.error('Tour not found:', data.hint);
  // Either seed tours or show error to user
}
```

### 5. Verify Payment Data is Stored

After initiating payment, verify the payment record exists:

```javascript
// After initiating payment
const initResponse = await fetch(`${API_URL}/api/payments/initiate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ booking_id: bookingId, phone_number: phoneNumber })
});
const initData = await initResponse.json();

// Verify payment was recorded
const statusResponse = await fetch(
  `${API_URL}/api/payments/status/${initData.checkout_request_id}`
);
const statusData = await statusResponse.json();

if (statusData.success) {
  console.log('Payment record created:', statusData.payment);
}
```

### 6. Poll Payment Status After STK Push

Daraja API callbacks may take time. Poll for status updates:

```javascript
async function waitForPayment(checkoutRequestId, maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch(
      `${API_URL}/api/payments/status/${checkoutRequestId}`
    );
    const data = await response.json();
    
    if (data.payment.status === 'completed') {
      return { success: true, payment: data.payment };
    }
    if (data.payment.status === 'failed') {
      return { success: false, error: data.payment.result_description };
    }
    
    // Wait 2 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  return { success: false, error: 'Payment timeout' };
}
```

### 7. List and Debug Payments

Use the payments list endpoint to debug payment issues:

```bash
# List all payments
curl "https://your-backend.up.railway.app/api/payments/"

# Filter by status
curl "https://your-backend.up.railway.app/api/payments/?status=failed"

# Filter by booking
curl "https://your-backend.up.railway.app/api/payments/?booking_id=123"
```

### 8. Error Code Reference

| Error Code | Description | Solution |
|------------|-------------|----------|
| `TOUR_NOT_FOUND` | Tour doesn't exist in database | Seed tours using `/api/tours/seed` |
| `BOOKING_NOT_FOUND` | Booking doesn't exist | Verify booking was created successfully |
| `PAYMENT_NOT_FOUND` | Payment record not found | Check checkout_request_id is correct |
| `SERVICE_NOT_CONFIGURED` | Daraja credentials missing | Configure DARAJA_* environment variables |
| `INVALID_PHONE` | Invalid M-Pesa phone number | Use format 07XXXXXXXX or 254XXXXXXXXX |
| `NO_DATA` | No JSON data in request | Ensure request includes JSON body |
| `NO_TOURS` | Empty tours array in bulk import | Provide at least one tour in the array |
| `DUPLICATE_TITLE` | Tour with same title exists | Use bulk-import with `update_existing: true` |

### 9. Database Migration Checklist

When migrating or setting up a new environment:

1. ✅ Verify database connection with `/health` endpoint
2. ✅ Seed default tours with `POST /api/tours/seed` (creates 30+ tours)
3. ✅ Or use `python scripts/init_tours.py` to initialize from command line
4. ✅ Verify tours exist with `GET /api/tours/`
5. ✅ Test payment configuration with `GET /api/payments/health`
6. ✅ Create a test booking to verify full flow

### 10. Database Initialization Script

For command-line database initialization, use the provided script:

```bash
# Initialize tours database (only adds missing tours)
python scripts/init_tours.py

# Force reinitialize (deletes existing tours and repopulates)
python scripts/init_tours.py --force

# Quiet mode (suppress output except errors)
python scripts/init_tours.py --quiet
```
