"""M-Pesa Daraja API integration for payments"""
from flask import Blueprint, jsonify, request, current_app
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import base64
from datetime import datetime
import os
import logging
from models import db, Payment, Booking

# Configure logger for payment module
logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

# Constants for API configuration
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5
RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504]


def create_session_with_retries():
    """Create a requests session with retry logic"""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=RETRY_STATUS_CODES,
        allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class DarajaAPI:
    """Daraja API integration class with enhanced error handling"""

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

        # Create session with retry logic
        self.session = create_session_with_retries()
        logger.info(f"DarajaAPI initialized with environment: {self.env}, base_url: {self.base_url}")

    def is_configured(self):
        """Check if all required credentials are configured"""
        return bool(
            self.consumer_key and
            self.consumer_secret and
            self.passkey and
            self.shortcode and
            self.callback_url
        )

    def get_configuration_status(self):
        """Return status of each configuration parameter"""
        return {
            'consumer_key_set': bool(self.consumer_key),
            'consumer_secret_set': bool(self.consumer_secret),
            'passkey_set': bool(self.passkey),
            'shortcode_set': bool(self.shortcode),
            'callback_url_set': bool(self.callback_url),
            'environment': self.env,
            'base_url': self.base_url,
            'is_configured': self.is_configured()
        }

    def get_access_token(self):
        """Get OAuth access token from Daraja API with enhanced error handling"""
        url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        credentials = base64.b64encode(
            f'{self.consumer_key}:{self.consumer_secret}'.encode()
        ).decode('utf-8')

        headers = {
            'Authorization': f'Basic {credentials}'
        }

        logger.debug(f"Requesting access token from {url}")

        try:
            response = self.session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)

            # Log response details for debugging
            logger.debug(f"Access token response status: {response.status_code}")

            if response.status_code == 401:
                logger.error("Authentication failed: Invalid consumer key or secret")
                raise DarajaAPIError(
                    "Authentication failed. Please verify your Daraja credentials.",
                    error_code="AUTH_FAILED",
                    status_code=401
                )

            if response.status_code != 200:
                logger.error(f"Access token request failed: {response.status_code} - {response.text}")
                raise DarajaAPIError(
                    f"Failed to get access token: HTTP {response.status_code}",
                    error_code="TOKEN_REQUEST_FAILED",
                    status_code=response.status_code,
                    details=response.text
                )

            data = response.json()
            access_token = data.get('access_token')

            if not access_token:
                logger.error(f"No access token in response: {data}")
                raise DarajaAPIError(
                    "No access token received from Daraja API",
                    error_code="NO_TOKEN",
                    details=str(data)
                )

            logger.info("Successfully obtained access token")
            return access_token

        except requests.exceptions.Timeout:
            logger.error(f"Timeout while requesting access token from {url}")
            raise DarajaAPIError(
                "Request to M-Pesa service timed out. Please try again.",
                error_code="TIMEOUT"
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error while requesting access token: {str(e)}")
            raise DarajaAPIError(
                "Unable to connect to M-Pesa service. Please check your internet connection.",
                error_code="CONNECTION_ERROR",
                details=str(e)
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while getting access token: {str(e)}")
            raise DarajaAPIError(
                f"Failed to communicate with M-Pesa service: {str(e)}",
                error_code="REQUEST_ERROR",
                details=str(e)
            )

    def generate_password(self, timestamp):
        """Generate password for STK Push"""
        data_to_encode = f'{self.shortcode}{self.passkey}{timestamp}'
        return base64.b64encode(data_to_encode.encode()).decode('utf-8')

    def stk_push(self, phone_number, amount, account_reference, description):
        """Initiate STK Push payment with enhanced error handling"""
        logger.info(f"Initiating STK Push for phone: {phone_number[-4:].rjust(len(phone_number), '*')}, amount: {amount}")

        # Validate amount
        if amount <= 0:
            raise DarajaAPIError(
                "Amount must be greater than zero",
                error_code="INVALID_AMOUNT"
            )

        if amount > 150000:  # M-Pesa transaction limit
            raise DarajaAPIError(
                "Amount exceeds M-Pesa transaction limit of KES 150,000",
                error_code="AMOUNT_EXCEEDS_LIMIT"
            )

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

        logger.debug(f"STK Push request to {url}")

        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)

            logger.debug(f"STK Push response status: {response.status_code}")

            # Check for specific error codes
            if response.status_code == 401:
                logger.error("STK Push authentication failed")
                raise DarajaAPIError(
                    "Payment authentication failed. Please contact support.",
                    error_code="AUTH_FAILED",
                    status_code=401
                )

            if response.status_code == 400:
                error_data = response.json() if response.text else {}
                error_message = error_data.get('errorMessage', 'Invalid request')
                logger.error(f"STK Push bad request: {error_message}")
                raise DarajaAPIError(
                    f"Payment request invalid: {error_message}",
                    error_code="BAD_REQUEST",
                    status_code=400,
                    details=error_data
                )

            if response.status_code != 200:
                logger.error(f"STK Push failed: {response.status_code} - {response.text}")
                raise DarajaAPIError(
                    f"Payment service error: HTTP {response.status_code}",
                    error_code="SERVICE_ERROR",
                    status_code=response.status_code,
                    details=response.text
                )

            result = response.json()
            logger.info(f"STK Push response: ResponseCode={result.get('ResponseCode')}")
            return result

        except requests.exceptions.Timeout:
            logger.error(f"Timeout during STK Push request")
            raise DarajaAPIError(
                "Payment request timed out. Please try again.",
                error_code="TIMEOUT"
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during STK Push: {str(e)}")
            raise DarajaAPIError(
                "Unable to connect to M-Pesa service. Please try again later.",
                error_code="CONNECTION_ERROR",
                details=str(e)
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during STK Push: {str(e)}")
            raise DarajaAPIError(
                f"Payment request failed: {str(e)}",
                error_code="REQUEST_ERROR",
                details=str(e)
            )

    def query_stk_status(self, checkout_request_id):
        """Query the status of an STK Push transaction with enhanced error handling"""
        logger.info(f"Querying STK status for checkout_request_id: {checkout_request_id}")

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

        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)

            logger.debug(f"STK Query response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"STK Query failed: {response.status_code} - {response.text}")
                raise DarajaAPIError(
                    f"Failed to query payment status: HTTP {response.status_code}",
                    error_code="QUERY_FAILED",
                    status_code=response.status_code,
                    details=response.text
                )

            result = response.json()
            logger.info(f"STK Query result: ResultCode={result.get('ResultCode')}")
            return result

        except requests.exceptions.Timeout:
            logger.error("Timeout while querying STK status")
            raise DarajaAPIError(
                "Payment status query timed out. Please try again.",
                error_code="TIMEOUT"
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error while querying STK status: {str(e)}")
            raise DarajaAPIError(
                "Unable to connect to M-Pesa service for status query.",
                error_code="CONNECTION_ERROR",
                details=str(e)
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while querying STK status: {str(e)}")
            raise DarajaAPIError(
                f"Failed to query payment status: {str(e)}",
                error_code="REQUEST_ERROR",
                details=str(e)
            )


class DarajaAPIError(Exception):
    """Custom exception for Daraja API errors with detailed information"""

    def __init__(self, message, error_code=None, status_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        """Convert error to dictionary for JSON response"""
        result = {
            'error': self.message,
            'error_code': self.error_code
        }
        if self.details:
            result['details'] = self.details
        return result


# Initialize Daraja API
daraja = DarajaAPI()


def format_phone_number(phone):
    """Format phone number to 254XXXXXXXXX format"""
    if phone is None:
        return None

    phone = str(phone).strip()
    phone = ''.join(filter(str.isdigit, phone))

    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+254'):
        phone = phone[1:]
    elif not phone.startswith('254'):
        phone = '254' + phone

    return phone


def validate_phone_number(phone):
    """Validate phone number format and return error message if invalid"""
    if not phone:
        return "Phone number is required"

    formatted = format_phone_number(phone)

    if len(formatted) != 12:
        return "Invalid phone number length. Must be 12 digits total (254 + 9 digits)."

    if not formatted.startswith('254'):
        return "Phone number must start with 254 or 0."

    # Validate Kenyan mobile prefixes (7XX or 1XX after 254)
    # Valid mobile prefixes: 254 7XX XXX XXX or 254 1XX XXX XXX
    mobile_prefix = formatted[3]
    if mobile_prefix not in ['7', '1']:
        return "Invalid phone number. Must be a Kenyan mobile number (07XX or 01XX)."

    return None


@payments_bp.route('/config/status', methods=['GET'])
def check_config_status():
    """Check M-Pesa configuration status (for debugging)"""
    try:
        config_status = daraja.get_configuration_status()

        return jsonify({
            'success': True,
            'config': config_status,
            'message': 'Configuration status retrieved successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error checking config status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check configuration status'
        }), 500


@payments_bp.route('/initiate', methods=['POST'])
def initiate_payment():
    """Initiate M-Pesa STK Push payment with enhanced validation and error handling"""
    try:
        data = request.get_json(silent=True)

        if not data:
            logger.warning("Payment initiation called with no data")
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'error_code': 'NO_DATA'
            }), 400

        # Validate required fields
        required_fields = ['booking_id', 'phone_number']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            logger.warning(f"Payment initiation missing fields: {missing_fields}")
            return jsonify({
                'success': False,
                'error': f'Missing required field(s): {", ".join(missing_fields)}',
                'error_code': 'MISSING_FIELDS',
                'missing_fields': missing_fields
            }), 400

        # Validate booking_id is a valid integer
        try:
            booking_id = int(data['booking_id'])
        except (ValueError, TypeError):
            logger.warning(f"Invalid booking_id format: {data['booking_id']}")
            return jsonify({
                'success': False,
                'error': 'Invalid booking ID format',
                'error_code': 'INVALID_BOOKING_ID'
            }), 400

        # Get booking
        booking = db.session.get(Booking, booking_id)
        if not booking:
            logger.warning(f"Booking not found: {booking_id}")
            return jsonify({
                'success': False,
                'error': 'Booking not found',
                'error_code': 'BOOKING_NOT_FOUND'
            }), 404

        if booking.payment_status == 'paid':
            logger.info(f"Booking {booking_id} is already paid")
            return jsonify({
                'success': False,
                'error': 'Booking is already paid',
                'error_code': 'ALREADY_PAID'
            }), 400

        # Format and validate phone number
        phone_number = format_phone_number(data['phone_number'])
        phone_error = validate_phone_number(data['phone_number'])
        if phone_error:
            logger.warning(f"Invalid phone number: {phone_error}")
            return jsonify({
                'success': False,
                'error': phone_error,
                'error_code': 'INVALID_PHONE',
                'hint': 'Use format: 07XXXXXXXX or 254XXXXXXXXX'
            }), 400

        # Check if Daraja credentials are configured
        if not daraja.is_configured():
            config_status = daraja.get_configuration_status()
            logger.error(f"Daraja not configured: {config_status}")
            # Build list of missing configuration
            missing_config = []
            if not config_status['consumer_key_set']:
                missing_config.append('DARAJA_CONSUMER_KEY')
            if not config_status['consumer_secret_set']:
                missing_config.append('DARAJA_CONSUMER_SECRET')
            if not config_status['passkey_set']:
                missing_config.append('DARAJA_PASSKEY')
            if not config_status['shortcode_set']:
                missing_config.append('DARAJA_SHORTCODE')
            if not config_status['callback_url_set']:
                missing_config.append('DARAJA_CALLBACK_URL')
            return jsonify({
                'success': False,
                'error': 'Payment service is not configured. Please contact support.',
                'error_code': 'SERVICE_NOT_CONFIGURED',
                'missing_configuration': missing_config,
                'hint': 'Configure Daraja API credentials in environment variables. Get credentials from https://developer.safaricom.co.ke/'
            }), 503

        # Validate amount
        if booking.total_amount <= 0:
            logger.error(f"Invalid booking amount: {booking.total_amount}")
            return jsonify({
                'success': False,
                'error': 'Invalid booking amount',
                'error_code': 'INVALID_AMOUNT'
            }), 400

        # Initiate STK Push
        account_reference = f'TWENDE-{booking.id}'
        description = f'Payment for tour booking #{booking.id}'

        logger.info(f"Initiating payment for booking {booking.id}, amount: {booking.total_amount}")

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

            logger.info(f"Payment initiated successfully. CheckoutRequestID: {result.get('CheckoutRequestID')}")

            return jsonify({
                'success': True,
                'message': 'Payment initiated. Please check your phone for the M-Pesa prompt.',
                'checkout_request_id': result.get('CheckoutRequestID'),
                'merchant_request_id': result.get('MerchantRequestID')
            }), 200
        else:
            error_message = result.get('errorMessage', result.get('ResponseDescription', 'Failed to initiate payment'))
            logger.error(f"STK Push returned error: {error_message}")
            return jsonify({
                'success': False,
                'error': error_message,
                'error_code': 'STK_PUSH_FAILED',
                'response_code': result.get('ResponseCode')
            }), 400

    except DarajaAPIError as e:
        db.session.rollback()
        logger.error(f"DarajaAPIError in initiate_payment: {e.message}")
        response = e.to_dict()
        response['success'] = False
        return jsonify(response), e.status_code or 500

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Unexpected error in initiate_payment: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again later.',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@payments_bp.route('/callback', methods=['POST'])
def payment_callback():
    """Handle M-Pesa payment callback with enhanced logging"""
    try:
        # Use silent=True to avoid raising exception for non-JSON content
        data = request.get_json(silent=True)

        if not data:
            logger.warning("Callback received with no data")
            return jsonify({'ResultCode': 1, 'ResultDesc': 'No data received'}), 400

        # Log callback data (mask sensitive info)
        logger.info(f"Payment callback received")
        logger.debug(f"Callback body keys: {list(data.keys())}")

        # Extract callback data
        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})

        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')

        logger.info(f"Callback: CheckoutRequestID={checkout_request_id}, ResultCode={result_code}")

        # Find payment record
        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()

        if not payment:
            logger.warning(f"Payment not found for checkout_request_id: {checkout_request_id}")
            return jsonify({'ResultCode': 1, 'ResultDesc': 'Payment not found'}), 404

        # Update payment record
        payment.result_code = result_code
        payment.result_description = result_desc

        if result_code == 0:
            # Payment successful
            logger.info(f"Payment successful for booking {payment.booking_id}")

            callback_metadata = stk_callback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])

            for item in items:
                name = item.get('Name')
                value = item.get('Value')

                if name == 'MpesaReceiptNumber':
                    payment.mpesa_receipt_number = value
                    logger.info(f"M-Pesa receipt: {value}")
                elif name == 'TransactionDate':
                    try:
                        payment.transaction_date = datetime.strptime(str(value), '%Y%m%d%H%M%S')
                    except ValueError:
                        logger.warning(f"Failed to parse transaction date: {value}")

            payment.status = 'completed'

            # Update booking
            booking = db.session.get(Booking, payment.booking_id)
            if booking:
                booking.payment_status = 'paid'
                booking.status = 'confirmed'
                booking.payment_reference = payment.mpesa_receipt_number
                logger.info(f"Booking {booking.id} confirmed with payment")
        else:
            # Payment failed or cancelled
            logger.warning(f"Payment failed for booking {payment.booking_id}: {result_desc}")
            payment.status = 'failed'

            # Update booking
            booking = db.session.get(Booking, payment.booking_id)
            if booking:
                booking.payment_status = 'failed'

        db.session.commit()

        return jsonify({'ResultCode': 0, 'ResultDesc': 'Callback received successfully'}), 200

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error processing payment callback: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': str(e)}), 500


@payments_bp.route('/status/<checkout_request_id>', methods=['GET'])
def check_payment_status(checkout_request_id):
    """Check payment status with enhanced error handling"""
    try:
        logger.info(f"Checking payment status for checkout_request_id: {checkout_request_id}")

        # Find payment in database
        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()

        if not payment:
            logger.warning(f"Payment not found: {checkout_request_id}")
            return jsonify({
                'success': False,
                'error': 'Payment not found',
                'error_code': 'PAYMENT_NOT_FOUND'
            }), 404

        # If payment is still pending, query Daraja API
        if payment.status == 'pending':
            logger.info(f"Payment still pending, querying Daraja API")
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
                    logger.info(f"Payment {checkout_request_id} confirmed via query")
                elif result_code_str:
                    payment.status = 'failed'
                    try:
                        payment.result_code = int(result_code_str)
                    except (ValueError, TypeError):
                        payment.result_code = None
                    payment.result_description = result.get('ResultDesc')
                    db.session.commit()
                    logger.info(f"Payment {checkout_request_id} failed via query: {result.get('ResultDesc')}")
            except DarajaAPIError as e:
                # If query fails, return current database status with warning
                logger.warning(f"Failed to query Daraja API for status: {e.message}")
            except Exception as e:
                # If query fails, return current database status
                logger.warning(f"Error querying payment status: {str(e)}")

        return jsonify({
            'success': True,
            'payment': payment.to_dict()
        }), 200

    except Exception as e:
        logger.exception(f"Error checking payment status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check payment status',
            'error_code': 'STATUS_CHECK_ERROR'
        }), 500


@payments_bp.route('/booking/<int:booking_id>', methods=['GET'])
def get_booking_payments(booking_id):
    """Get all payments for a booking with enhanced error handling"""
    try:
        logger.info(f"Getting payments for booking {booking_id}")

        # Verify booking exists
        booking = db.session.get(Booking, booking_id)
        if not booking:
            logger.warning(f"Booking not found: {booking_id}")
            return jsonify({
                'success': False,
                'error': 'Booking not found',
                'error_code': 'BOOKING_NOT_FOUND'
            }), 404

        payments = Payment.query.filter_by(booking_id=booking_id).all()

        return jsonify({
            'success': True,
            'payments': [payment.to_dict() for payment in payments],
            'count': len(payments)
        }), 200

    except Exception as e:
        logger.exception(f"Error getting booking payments: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve payments',
            'error_code': 'RETRIEVAL_ERROR'
        }), 500


@payments_bp.route('/', methods=['GET'])
def list_payments():
    """List all payments with optional filtering and pagination.
    
    Query Parameters:
        status: Filter by payment status (initiated, pending, completed, failed, cancelled)
        booking_id: Filter by booking ID
        page: Page number for pagination (default: 1)
        per_page: Results per page (default: 20, max: 100)
    
    Returns:
        JSON object with payments list and pagination info
    """
    try:
        status = request.args.get('status')
        booking_id = request.args.get('booking_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20

        query = Payment.query

        # Apply filters
        if status:
            query = query.filter_by(status=status)
        if booking_id:
            query = query.filter_by(booking_id=booking_id)

        # Order by most recent first
        query = query.order_by(Payment.created_at.desc())

        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'payments': [payment.to_dict() for payment in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        logger.exception(f"Error listing payments: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to list payments',
            'error_code': 'LIST_ERROR'
        }), 500


@payments_bp.route('/health', methods=['GET'])
def payment_service_health():
    """Check M-Pesa payment service health and connectivity"""
    try:
        config_status = daraja.get_configuration_status()

        health_status = {
            'success': True,
            'service': 'M-Pesa Payment Gateway',
            'configured': config_status['is_configured'],
            'environment': config_status['environment'],
            'base_url': config_status['base_url']
        }

        # If configured, try to get access token to verify connectivity
        if config_status['is_configured']:
            try:
                access_token = daraja.get_access_token()
                health_status['connectivity'] = 'connected'
                health_status['token_valid'] = bool(access_token)
            except DarajaAPIError as e:
                health_status['connectivity'] = 'error'
                health_status['connectivity_error'] = e.message
                health_status['error_code'] = e.error_code
                health_status['success'] = False
        else:
            health_status['connectivity'] = 'not_tested'
            health_status['message'] = 'Service not configured - cannot test connectivity'
            # Provide hints for missing configuration
            missing_config = []
            if not config_status['consumer_key_set']:
                missing_config.append('DARAJA_CONSUMER_KEY')
            if not config_status['consumer_secret_set']:
                missing_config.append('DARAJA_CONSUMER_SECRET')
            if not config_status['passkey_set']:
                missing_config.append('DARAJA_PASSKEY')
            if not config_status['shortcode_set']:
                missing_config.append('DARAJA_SHORTCODE')
            if not config_status['callback_url_set']:
                missing_config.append('DARAJA_CALLBACK_URL')
            if missing_config:
                health_status['missing_configuration'] = missing_config
                health_status['hint'] = 'Set the missing environment variables in .env or your deployment platform'

        return jsonify(health_status), 200 if health_status['success'] else 503

    except Exception as e:
        logger.exception(f"Error checking payment service health: {str(e)}")
        return jsonify({
            'success': False,
            'service': 'M-Pesa Payment Gateway',
            'error': 'Health check failed',
            'error_code': 'HEALTH_CHECK_ERROR'
        }), 500


@payments_bp.route('/test-connection', methods=['POST'])
def test_daraja_connection():
    """Test Daraja API connection with detailed diagnostics.
    
    This endpoint performs a comprehensive connectivity test to the Daraja API
    and returns detailed diagnostic information useful for debugging 503 errors.
    
    Returns:
        JSON object with detailed connectivity test results including:
        - Configuration status
        - OAuth token acquisition result
        - Network connectivity status
        - Detailed error information if connection fails
    """
    try:
        logger.info("Starting Daraja API connection test")
        config_status = daraja.get_configuration_status()
        
        result = {
            'success': False,
            'test_timestamp': datetime.now().isoformat(),
            'configuration': config_status,
            'tests': {}
        }
        
        # Test 1: Configuration check
        result['tests']['configuration'] = {
            'passed': config_status['is_configured'],
            'message': 'All required credentials are configured' if config_status['is_configured'] 
                       else 'Missing required Daraja credentials'
        }
        
        if not config_status['is_configured']:
            missing = []
            if not config_status['consumer_key_set']:
                missing.append('DARAJA_CONSUMER_KEY')
            if not config_status['consumer_secret_set']:
                missing.append('DARAJA_CONSUMER_SECRET')
            if not config_status['passkey_set']:
                missing.append('DARAJA_PASSKEY')
            if not config_status['shortcode_set']:
                missing.append('DARAJA_SHORTCODE')
            if not config_status['callback_url_set']:
                missing.append('DARAJA_CALLBACK_URL')
            result['tests']['configuration']['missing_variables'] = missing
            result['tests']['configuration']['hint'] = (
                'Set these environment variables in your .env file or deployment platform. '
                'Get credentials from https://developer.safaricom.co.ke/'
            )
            return jsonify(result), 503
        
        # Test 2: Network connectivity to Daraja API
        result['tests']['network'] = {'passed': False, 'message': 'Testing...'}
        try:
            # Simple HEAD request to check if the API is reachable
            head_response = daraja.session.head(daraja.base_url, timeout=10)
            result['tests']['network'] = {
                'passed': True,
                'message': f'Daraja API reachable at {daraja.base_url}',
                'status_code': head_response.status_code
            }
        except requests.exceptions.Timeout:
            result['tests']['network'] = {
                'passed': False,
                'message': 'Connection to Daraja API timed out',
                'error': 'TIMEOUT',
                'hint': 'Check your network connection and firewall settings'
            }
            return jsonify(result), 503
        except requests.exceptions.ConnectionError as e:
            result['tests']['network'] = {
                'passed': False,
                'message': 'Cannot connect to Daraja API',
                'error': 'CONNECTION_ERROR',
                'details': str(e),
                'hint': 'Verify network connectivity and that the Daraja API URL is correct'
            }
            return jsonify(result), 503
        
        # Test 3: OAuth Authentication
        result['tests']['authentication'] = {'passed': False, 'message': 'Testing...'}
        try:
            access_token = daraja.get_access_token()
            result['tests']['authentication'] = {
                'passed': True,
                'message': 'Successfully authenticated with Daraja API',
                'token_received': bool(access_token)
            }
            result['success'] = True
        except DarajaAPIError as e:
            result['tests']['authentication'] = {
                'passed': False,
                'message': e.message,
                'error_code': e.error_code,
                'hint': 'Verify your DARAJA_CONSUMER_KEY and DARAJA_CONSUMER_SECRET are correct'
            }
            if e.details:
                result['tests']['authentication']['details'] = str(e.details)
            return jsonify(result), 503
        
        logger.info("Daraja API connection test completed successfully")
        return jsonify(result), 200
        
    except Exception as e:
        logger.exception(f"Error during Daraja connection test: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Connection test failed unexpectedly',
            'error_code': 'TEST_ERROR',
            'details': str(e)
        }), 500
