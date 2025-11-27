# Daraja Files Directory

This directory is for hosting static Daraja (M-Pesa payment) related HTML, JavaScript, and CSS files.

## Usage

Place your Daraja-related static files in this directory. They will be served at `/daraja/*` URLs.

### Example Structure

```
public/daraja/
├── index.html          # Main Daraja page
├── payment.html        # Payment form page
├── callback.html       # Callback display page
├── css/
│   └── styles.css      # Daraja-specific styles
└── js/
    └── daraja.js       # Daraja frontend logic
```

### Accessing Files

- `https://your-domain.com/daraja/index.html`
- `https://your-domain.com/daraja/payment.html`
- `https://your-domain.com/daraja/css/styles.css`

## API Integration

The Daraja static files should interact with the following backend API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/initiate` | Initiate M-Pesa STK Push |
| GET | `/api/payments/status/<checkout_request_id>` | Check payment status |
| GET | `/api/payments/booking/<booking_id>` | Get payments for a booking |

### Example JavaScript (daraja.js)

```javascript
// Initiate STK Push payment
async function initiatePayment(bookingId, phoneNumber) {
    const response = await fetch('/api/payments/initiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            booking_id: bookingId,
            phone_number: phoneNumber
        })
    });
    return response.json();
}

// Check payment status
async function checkPaymentStatus(checkoutRequestId) {
    const response = await fetch(`/api/payments/status/${checkoutRequestId}`);
    return response.json();
}
```

## Configuration

Ensure the following environment variables are set in `.env`:

```bash
DARAJA_ENV=sandbox
DARAJA_CONSUMER_KEY=your_consumer_key
DARAJA_CONSUMER_SECRET=your_consumer_secret
DARAJA_PASSKEY=your_passkey
DARAJA_SHORTCODE=174379
DARAJA_CALLBACK_URL=https://your-backend-url.com/api/payments/callback
```
