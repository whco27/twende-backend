"""M-Pesa Daraja API integration for payments"""
from flask import Blueprint, jsonify, request, current_app
import requests
import base64
from datetime import datetime
import os
from models import db, Payment, Booking

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')


class DarajaAPI:
    """Daraja API integration class"""

    def __init__(self):
        self.consumer_key = os.getenv('DARAJA_CONSUMER_KEY', '')
        self.consumer_secret = os.getenv('DARAJA_CONSUMER_SECRET', '')
        self.passkey = os.getenv('DARAJA_PASSKEY', '')
        self.shortcode = os.getenv('DARAJA_SHORTCODE', '')
        self.callback_url = os.getenv('DARAJA_CALLBACK_URL', '')
        self.env = os.getenv('DARAJA_ENV', 'sandbox')

        # Set base URL based on environment
        if self.env == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'

    def get_access_token(self):
        """Get OAuth access token from Daraja API"""
        try:
            url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
            credentials = base64.b64encode(
                f'{self.consumer_key}:{self.consumer_secret}'.encode()
            ).decode('utf-8')

            headers = {
                'Authorization': f'Basic {credentials}'
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            return response.json().get('access_token')
        except requests.exceptions.RequestException as e:
            raise Exception(f'Failed to get access token: {str(e)}')

    def generate_password(self, timestamp):
        """Generate password for STK Push"""
        data_to_encode = f'{self.shortcode}{self.passkey}{timestamp}'
        return base64.b64encode(data_to_encode.encode()).decode('utf-8')

    def stk_push(self, phone_number, amount, account_reference, description):
        """Initiate STK Push payment"""
        try:
            access_token = self.get_access_token()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)

            url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),
                'PartyA': phone_number,
                'PartyB': self.shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': description
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f'STK Push failed: {str(e)}')

    def query_stk_status(self, checkout_request_id):
        """Query the status of an STK Push transaction"""
        try:
            access_token = self.get_access_token()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)

            url = f'{self.base_url}/mpesa/stkpushquery/v1/query'

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }

            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f'STK Query failed: {str(e)}')


# Initialize Daraja API
daraja = DarajaAPI()


def format_phone_number(phone):
    """Format phone number to 254XXXXXXXXX format"""
    phone = str(phone).strip()
    phone = ''.join(filter(str.isdigit, phone))

    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+254'):
        phone = phone[1:]
    elif not phone.startswith('254'):
        phone = '254' + phone

    return phone


@payments_bp.route('/initiate', methods=['POST'])
def initiate_payment():
    """Initiate M-Pesa STK Push payment"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        required_fields = ['booking_id', 'phone_number']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Get booking
        booking = db.session.get(Booking, data['booking_id'])
        if not booking:
            return jsonify({
                'success': False,
                'error': 'Booking not found'
            }), 404

        if booking.payment_status == 'paid':
            return jsonify({
                'success': False,
                'error': 'Booking is already paid'
            }), 400

        # Format phone number
        phone_number = format_phone_number(data['phone_number'])

        # Validate phone number format
        if len(phone_number) != 12 or not phone_number.startswith('254'):
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format. Use format: 07XXXXXXXX or 254XXXXXXXXX'
            }), 400

        # Check if Daraja credentials are configured
        if not daraja.consumer_key or not daraja.consumer_secret:
            return jsonify({
                'success': False,
                'error': 'Payment service is not configured. Please contact support.'
            }), 503

        # Initiate STK Push
        account_reference = f'TWENDE-{booking.id}'
        description = f'Payment for tour booking #{booking.id}'

        result = daraja.stk_push(
            phone_number=phone_number,
            amount=booking.total_amount,
            account_reference=account_reference,
            description=description
        )

        # Check response
        if result.get('ResponseCode') == '0':
            # Create payment record
            payment = Payment(
                booking_id=booking.id,
                merchant_request_id=result.get('MerchantRequestID'),
                checkout_request_id=result.get('CheckoutRequestID'),
                phone_number=phone_number,
                amount=booking.total_amount,
                status='pending'
            )
            db.session.add(payment)

            # Update booking payment status
            booking.payment_status = 'pending'
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Payment initiated. Please check your phone for the M-Pesa prompt.',
                'checkout_request_id': result.get('CheckoutRequestID'),
                'merchant_request_id': result.get('MerchantRequestID')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('errorMessage', 'Failed to initiate payment')
            }), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payments_bp.route('/callback', methods=['POST'])
def payment_callback():
    """Handle M-Pesa payment callback"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'ResultCode': 1, 'ResultDesc': 'No data received'}), 400

        # Extract callback data
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})

        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')

        # Find payment record
        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()

        if not payment:
            return jsonify({'ResultCode': 1, 'ResultDesc': 'Payment not found'}), 404

        # Update payment record
        payment.result_code = result_code
        payment.result_description = result_desc

        if result_code == 0:
            # Payment successful
            callback_metadata = stk_callback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])

            for item in items:
                name = item.get('Name')
                value = item.get('Value')

                if name == 'MpesaReceiptNumber':
                    payment.mpesa_receipt_number = value
                elif name == 'TransactionDate':
                    try:
                        payment.transaction_date = datetime.strptime(str(value), '%Y%m%d%H%M%S')
                    except ValueError:
                        pass

            payment.status = 'completed'

            # Update booking
            booking = db.session.get(Booking, payment.booking_id)
            if booking:
                booking.payment_status = 'paid'
                booking.status = 'confirmed'
                booking.payment_reference = payment.mpesa_receipt_number
        else:
            # Payment failed or cancelled
            payment.status = 'failed'

            # Update booking
            booking = db.session.get(Booking, payment.booking_id)
            if booking:
                booking.payment_status = 'failed'

        db.session.commit()

        return jsonify({'ResultCode': 0, 'ResultDesc': 'Callback received successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'ResultCode': 1, 'ResultDesc': str(e)}), 500


@payments_bp.route('/status/<checkout_request_id>', methods=['GET'])
def check_payment_status(checkout_request_id):
    """Check payment status"""
    try:
        # Find payment in database
        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()

        if not payment:
            return jsonify({
                'success': False,
                'error': 'Payment not found'
            }), 404

        # If payment is still pending, query Daraja API
        if payment.status == 'pending':
            try:
                result = daraja.query_stk_status(checkout_request_id)
                result_code = result.get('ResultCode')

                # Normalize result_code to string for consistent comparison
                result_code_str = str(result_code) if result_code is not None else None

                if result_code_str == '0':
                    payment.status = 'completed'
                    booking = db.session.get(Booking, payment.booking_id)
                    if booking:
                        booking.payment_status = 'paid'
                        booking.status = 'confirmed'
                    db.session.commit()
                elif result_code_str:
                    payment.status = 'failed'
                    try:
                        payment.result_code = int(result_code_str)
                    except (ValueError, TypeError):
                        payment.result_code = None
                    payment.result_description = result.get('ResultDesc')
                    db.session.commit()
            except Exception:
                # If query fails, return current database status
                pass

        return jsonify({
            'success': True,
            'payment': payment.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@payments_bp.route('/booking/<int:booking_id>', methods=['GET'])
def get_booking_payments(booking_id):
    """Get all payments for a booking"""
    try:
        payments = Payment.query.filter_by(booking_id=booking_id).all()

        return jsonify({
            'success': True,
            'payments': [payment.to_dict() for payment in payments]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
