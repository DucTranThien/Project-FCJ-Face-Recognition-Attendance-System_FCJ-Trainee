from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
import os
import base64
from io import BytesIO
from datetime import datetime
import json
from functools import wraps
from services.s3_service import S3Service
from services.rekognition_service import RekognitionService
from services.dynamodb_service import DynamoDBService
from services.email_service import EmailService
from services.settings_service import SettingsService

# Load environment variables
if os.path.exists('.env'):
    load_dotenv()

def get_user_avatar_url(user):
    """Get user avatar URL with fallback"""
    if user and user.get('image_url'):
        return user['image_url']
    return '/static/images/default-avatar.svg'


# Initialize Flask app for Lambda compatibility
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fcj-checkin-secret-key-2024')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize services
s3_service = S3Service()
rekognition_service = RekognitionService()
db_service = DynamoDBService()
email_service = EmailService()
settings_service = SettingsService()

# Template filters for safe data access
@app.template_filter('safe_get')
def safe_get(dictionary, key, default=''):
    """Safely get value from dictionary"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, default)
    return default

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            flash('Admin access required')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        username = request.form['username']
        full_name = request.form['full_name']
        password = request.form['password']
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address')
            return render_template('register.html')
        
        # Check if email already exists
        if db_service.get_user_by_email(email):
            flash('Email address already registered')
            return render_template('register.html')
        
        # Check if user exists
        if db_service.get_user(username):
            flash('Username already exists')
            return render_template('register.html')
        
        # Handle image input - prioritize file upload over camera
        image_file = None
        
        # Check for uploaded file first
        if 'face_image_file' in request.files:
            uploaded_file = request.files['face_image_file']
            if uploaded_file and uploaded_file.filename and uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Reset file pointer to beginning
                uploaded_file.seek(0)
                image_file = uploaded_file

        
        # If no file upload, check for camera capture
        if not image_file and 'face_image_data' in request.form and request.form['face_image_data']:
            face_image_data = request.form['face_image_data']
            if face_image_data.startswith('data:image/'):
                try:
                    image_data = base64.b64decode(face_image_data.split(',')[1])
                    image_file = BytesIO(image_data)

                except Exception as e:
                    pass
        
        if not image_file:
            flash('Please provide a face image (upload file or use camera)')
            return render_template('register.html')
        
        # Upload image to S3
        try:
            image_url = s3_service.upload_image(image_file, username)
            if not image_url:
                flash('Failed to upload image to cloud storage')
                return render_template('register.html')

        except Exception as e:
            print(f"S3 upload error during registration: {e}")
            flash('Failed to upload image to cloud storage. Please try again.')
            return render_template('register.html')
        
        # Save user to DynamoDB with explicit 'user' role
        if db_service.create_user(username, full_name, password, image_url, email=email, role='user'):
            return redirect(url_for('register_success', username=username))
        else:
            flash('Registration failed')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db_service.get_user(username)
        if user and user['password'] == password:
            # Check if user needs to update email (for existing users)
            user_email = user.get('email', '').strip()
            if not user_email or '@' not in user_email:
                # Store pending login data
                session['pending_login'] = {
                    'username': username,
                    'full_name': user['full_name'],
                    'role': user.get('role', 'user'),
                    'needs_email': True
                }
                flash('Please add your email address to continue with secure login', 'warning')
                return redirect(url_for('edit_profile'))
            
            # Validate email before sending OTP
            user_email = user.get('email', '').strip()
            if not user_email or '@' not in user_email:
                flash('Invalid email address in your profile. Please update your profile.', 'error')
                return redirect(url_for('edit_profile'))
            
            # Generate and send OTP
            otp = email_service.generate_otp()
            success, error_message = email_service.send_otp_email(user_email, otp, user['full_name'])
            
            if success:
                # Store OTP and pending login data
                email_service.store_otp(session, otp, user_email)
                session['pending_login'] = {
                    'username': username,
                    'full_name': user['full_name'],
                    'email': user_email,
                    'role': user.get('role', 'user')
                }
                flash(f'Verification code sent to {user_email}', 'info')
                return redirect(url_for('verify_otp'))
            else:
                flash(f'Failed to send verification code: {error_message}', 'error')
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        if 'pending_login' in session:
            flash('Please complete email verification to continue')
            return redirect(url_for('verify_otp'))
        return redirect(url_for('login'))
    
    user = db_service.get_user(session['username'])
    if not user:
        return redirect(url_for('login'))
    
    # Get today's sessions (morning/evening)
    today_sessions = db_service.get_today_sessions(session['username'])
    
    # Get user summary data
    summary = db_service.get_user_checkin_summary(session['username'])
    
    # Get current time for greeting
    now = datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    return render_template('dashboard.html', 
                         user=user, 
                         today_sessions=today_sessions,
                         summary=summary,
                         greeting=greeting,
                         current_time=now.strftime('%Y-%m-%d %H:%M'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = db_service.get_user(session['username'])
    if not user:
        return redirect(url_for('login'))
    
    # Get user summary for quick stats
    summary = db_service.get_user_checkin_summary(session['username'], 30)
    
    return render_template('profile.html', user=user, summary=summary)

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    # Safe session handling - get username from either full login or pending login
    current_username = session.get('username')
    is_pending_login = False
    
    if not current_username and 'pending_login' in session:
        # User pending OTP verification
        pending = session['pending_login']
        current_username = pending.get('username')
        is_pending_login = True
        # Show message for users who need to add email
        if pending.get('needs_email'):
            flash('Email address is required for secure login. Please add your email below.', 'info')
    
    if not current_username:
        # No valid session
        flash('Please log in to access your profile', 'error')
        return redirect(url_for('login'))
    
    # Get user from database
    user = db_service.get_user(current_username)
    if not user:
        session.clear()
        flash('User account not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not full_name:
            flash('Full name is required')
            return render_template('edit_profile.html', user=user)
        
        # Validate email if provided
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                flash('Please enter a valid email address')
                return render_template('edit_profile.html', user=user)
            
            # Check if email is already used by another user
            existing_user = db_service.get_user_by_email(email)
            if existing_user and existing_user['username'] != current_username:
                flash('Email address already in use by another account', 'error')
                return render_template('edit_profile.html', user=user)
        
        # Password validation
        if password and password != confirm_password:
            flash('Passwords do not match')
            return render_template('edit_profile.html', user=user)
        
        # Handle image update
        image_url = user.get('image_url')
        
        # Check for uploaded file first
        if 'face_image_file' in request.files and request.files['face_image_file'].filename:
            uploaded_file = request.files['face_image_file']
            if uploaded_file and uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                new_image_url = s3_service.upload_image(uploaded_file, current_username)
                if new_image_url:
                    image_url = new_image_url
        
        # Check for camera capture
        elif 'face_image_data' in request.form and request.form['face_image_data']:
            face_image_data = request.form['face_image_data']
            image_data = base64.b64decode(face_image_data.split(',')[1])
            image_file = BytesIO(image_data)
            new_image_url = s3_service.upload_image(image_file, current_username)
            if new_image_url:
                image_url = new_image_url
        
        # Update user in database
        try:
            update_expression = 'SET full_name = :name, image_url = :img, email = :email'
            expression_values = {
                ':name': full_name,
                ':img': image_url,
                ':email': email
            }
            
            if password:
                update_expression += ', password = :pwd'
                expression_values[':pwd'] = password
            
            db_service.users_table.update_item(
                Key={'username': current_username},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            # Update session based on login state
            if is_pending_login and 'pending_login' in session:
                # Complete login for users who were updating email
                pending = session['pending_login']
                session['username'] = current_username
                session['full_name'] = full_name
                session['email'] = email
                session['role'] = pending.get('role', 'user')
                session.pop('pending_login', None)
                flash('Profile updated and login completed!', 'success')
                # Redirect based on role
                if session['role'] == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                # Regular profile update for logged-in user
                session['full_name'] = full_name
                session['email'] = email
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
            
        except Exception as e:
            flash('Failed to update profile')
            return render_template('edit_profile.html', user=user)
    
    return render_template('edit_profile.html', user=user)

@app.route('/leaderboard')
def leaderboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    leaderboard_data = db_service.get_leaderboard_data()
    
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get user's full check-in history
    try:
        response = db_service.checkin_table.query(
            KeyConditionExpression='username = :username',
            ExpressionAttributeValues={':username': session['username']},
            ScanIndexForward=False
        )
        checkins = response.get('Items', [])
    except:
        checkins = []
    
    return render_template('history.html', checkins=checkins)

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if 'username' not in session:
        if 'pending_login' in session:
            flash('Please complete email verification to continue')
            return redirect(url_for('verify_otp'))
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        face_image_data = request.form.get('face_image_data')
        
        if not face_image_data:
            flash('Please capture a face image')
            return render_template('checkin.html')
        
        # Check if user can check-in now
        checkin_status = db_service.can_checkin_now(session['username'])
        if not checkin_status['can_checkin']:
            session['checkin_result'] = {
                'similarity': 0,
                'status': 'blocked',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': checkin_status['message']
            }
            return redirect(url_for('checkin_success'))
        
        # Convert base64 to BytesIO
        image_data = base64.b64decode(face_image_data.split(',')[1])
        image_file = BytesIO(image_data)
        
        # Compare faces using AWS Rekognition
        similarity = rekognition_service.compare_faces(session['username'], image_file)
        
        # Strict validation: Only save if similarity >= 95%
        if similarity >= 95.0:
            status = 'success'
        else:
            # Don't save failed attempts - allow retry
            session['checkin_result'] = {
                'similarity': similarity,
                'status': 'failed',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': f'Face recognition failed. Similarity: {similarity:.1f}% (Required: ≥95%)',
                'can_retry': True,
                'threshold': 95.0,
                'session_type': checkin_status.get('session_type', 'unknown')
            }
            return redirect(url_for('checkin_success'))
        
        # Save successful check-in (similarity already validated above)
        save_result = db_service.save_checkin(session['username'], similarity, status)
        now = datetime.now()
        
        # Validate save_result structure
        if not save_result or not isinstance(save_result, dict):
            session['checkin_result'] = {
                'similarity': similarity,
                'status': 'error',
                'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Unexpected error during check-in. Please try again.',
                'session_type': checkin_status.get('session_type', 'unknown')
            }
            return redirect(url_for('checkin_success'))
        
        if 'error' in save_result:
            if save_result.get('error') == 'recognition_failed':
                # Face recognition failed - allow retry
                session['checkin_result'] = {
                    'similarity': similarity,
                    'status': 'failed',
                    'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'message': save_result.get('message', 'Face recognition failed'),
                    'can_retry': True,
                    'threshold': save_result.get('threshold', 95),
                    'session_type': checkin_status.get('session_type', 'unknown')
                }
            elif save_result.get('error') == 'duplicate':
                # Already completed this session
                session_type = save_result.get('session_type', checkin_status.get('session_type', 'unknown'))
                session['checkin_result'] = {
                    'similarity': similarity,
                    'status': 'duplicate',
                    'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'message': f'You have already completed {session_type} check-in today',
                    'session_type': session_type
                }
            else:
                # Other error types
                session['checkin_result'] = {
                    'similarity': similarity,
                    'status': 'error',
                    'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'message': save_result.get('message', 'Check-in failed'),
                    'session_type': checkin_status.get('session_type', 'unknown')
                }
            return redirect(url_for('checkin_success'))
        
        # Success case - validate required fields
        if save_result and 'session_type' in save_result and 'time' in save_result:
            session_type = save_result['session_type']
            check_time = save_result['time']
            
            # Create success message
            if session_type == 'morning':
                message = f'Morning check-in completed successfully at {check_time}'
            elif session_type == 'evening':
                message = f'Evening check-out completed successfully at {check_time}'
            else:
                message = f'Check-in completed at {check_time}'
        
            # Store result in session for success page
            session['checkin_result'] = {
                'similarity': similarity,
                'status': status,
                'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                'session_type': session_type,
                'check_type': save_result.get('check_type', session_type),
                'time': check_time,
                'message': message
            }
        else:
            # Fallback for incomplete success result
            session['checkin_result'] = {
                'similarity': similarity,
                'status': 'error',
                'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
                'message': 'Check-in processing incomplete. Please try again.',
                'session_type': checkin_status.get('session_type', 'unknown')
            }
        
        return redirect(url_for('checkin_success'))
    
    # GET request - check if user can check-in and pass status to template
    checkin_status = db_service.can_checkin_now(session['username'])
    
    # Add settings data to checkin_status
    if checkin_status:
        checkin_status['time_windows'] = settings_service.get_time_windows()
        checkin_status['similarity_threshold'] = settings_service.get_similarity_threshold()
    
    return render_template('checkin.html', checkin_status=checkin_status)

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_login' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        entered_otp = request.form['otp']
        success, message = email_service.verify_otp(session, entered_otp)
        
        if success:
            # Complete login
            pending = session['pending_login']
            session['username'] = pending['username']
            session['full_name'] = pending['full_name']
            session['email'] = pending['email']
            session['role'] = pending['role']
            
            # Clear OTP data
            email_service.clear_otp(session)
            
            flash('Login successful!', 'success')
            # Redirect based on role
            if session['role'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('verify_otp.html')

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'pending_login' not in session:
        return {'error': 'No pending login session'}, 400
    
    if not email_service.can_resend_otp(session):
        return {'error': 'Please wait 30 seconds before requesting a new code'}, 429
    
    pending = session['pending_login']
    user_email = pending.get('email', '').strip()
    
    if not user_email or '@' not in user_email:
        return {'error': 'Invalid email address'}, 400
    
    otp = email_service.generate_otp()
    success, error_message = email_service.send_otp_email(user_email, otp, pending['full_name'])
    
    if success:
        email_service.store_otp(session, otp, user_email)
        return {'success': f'New verification code sent to {user_email}'}
    else:
        return {'error': f'Failed to send code: {error_message}'}, 500

@app.route('/register/success/<username>')
def register_success(username):
    user = db_service.get_user(username)
    if not user:
        return redirect(url_for('index'))
    return render_template('register_success.html', user=user)

@app.route('/checkin/success')
def checkin_success():
    if 'username' not in session or 'checkin_result' not in session:
        return redirect(url_for('index'))
    
    user = db_service.get_user(session['username'])
    result = session['checkin_result']
    
    # Don't clear result from session if it's a failed attempt (allow retry)
    if not result.get('can_retry', False):
        session.pop('checkin_result', None)
    
    return render_template('checkin_success.html', user=user, result=result)



@app.route('/admin')
@admin_required
def admin():
    # Calculate admin statistics
    from datetime import datetime, timedelta
    
    # Get all users and checkins
    all_users = db_service.get_all_users()
    all_checkins = db_service.get_all_checkins()
    
    # Today's statistics
    today = datetime.now().date().isoformat()
    today_checkins = [c for c in all_checkins if c.get('date', c['checkin_time'][:10]) == today]
    
    # Calculate stats
    admin_stats = {
        'total_users': len([u for u in all_users if u.get('role') != 'admin']),
        'today_checkins': len(today_checkins),
        'success_rate': round((len([c for c in today_checkins if c['status'] == 'success']) / len(today_checkins) * 100) if today_checkins else 0, 1),
        'missed_checkins': len(all_users) - len(set(c['username'] for c in today_checkins)),
        'avg_similarity': round(sum(float(c.get('similarity', 0)) for c in today_checkins if c['status'] == 'success') / len([c for c in today_checkins if c['status'] == 'success']) if [c for c in today_checkins if c['status'] == 'success'] else 0, 1),
        'completion_rate': round((len(today_checkins) / len(all_users) * 100) if all_users else 0, 1)
    }
    
    return render_template('admin_dashboard.html', admin_stats=admin_stats)

@app.route('/admin/profile')
@admin_required
def admin_profile():
    # Get admin user information
    admin_user = db_service.get_user(session['username'])
    
    # Admin information
    admin_info = {
        'full_name': admin_user.get('full_name', 'System Administrator'),
        'username': admin_user.get('username', 'admin'),
        'email': admin_user.get('email', 'admin@fcj-system.com'),
        'role': 'System Administrator',
        'created_at': admin_user.get('created_at')
    }
    
    # Admin statistics
    all_users = db_service.get_all_users()
    admin_stats = {
        'total_users': len([u for u in all_users if u.get('role') != 'admin']),
        'system_uptime': '99.9%'
    }
    
    # Recent admin activities (mock data for demonstration)
    admin_activities = [
        {
            'type': 'user',
            'icon': 'person-plus',
            'title': 'New User Registration',
            'description': 'Approved new user account registration and profile setup',
            'timestamp': '2 hours ago'
        },
        {
            'type': 'report',
            'icon': 'file-earmark-text',
            'title': 'Monthly Report Generated',
            'description': 'Generated and exported monthly attendance report for management review',
            'timestamp': '1 day ago'
        },
        {
            'type': 'system',
            'icon': 'gear',
            'title': 'System Configuration Update',
            'description': 'Updated attendance policy settings and notification preferences',
            'timestamp': '2 days ago'
        },
        {
            'type': 'security',
            'icon': 'shield-check',
            'title': 'Security Audit Completed',
            'description': 'Performed routine security audit and updated access permissions',
            'timestamp': '3 days ago'
        },
        {
            'type': 'user',
            'icon': 'people',
            'title': 'User Management Review',
            'description': 'Reviewed user accounts and updated role assignments',
            'timestamp': '5 days ago'
        }
    ]
    
    return render_template('admin_profile.html', 
                         admin_info=admin_info, 
                         admin_stats=admin_stats, 
                         admin_activities=admin_activities)

@app.route('/api/checkin-status')
def api_checkin_status():
    if 'username' not in session:
        return {'error': 'Not authenticated', 'authenticated': False}, 200
    
    today_sessions = db_service.get_today_sessions(session['username'])
    summary = db_service.get_user_checkin_summary(session['username'], 7)
    
    return {
        'today_sessions': {
            'morning': {
                'completed': bool(today_sessions['morning']),
                'time': today_sessions['morning']['checkin_time'][11:19] if today_sessions['morning'] else None,
                'status': today_sessions['morning']['status'] if today_sessions['morning'] else None
            },
            'evening': {
                'completed': bool(today_sessions['evening']),
                'time': today_sessions['evening']['checkin_time'][11:19] if today_sessions['evening'] else None,
                'status': today_sessions['evening']['status'] if today_sessions['evening'] else None
            }
        },
        'recent_checkins': summary['recent_checkins'][:3]
    }

@app.route('/api/calendar-data')
def api_calendar_data():
    if 'username' not in session:
        # Return empty calendar data for unauthenticated users
        from datetime import datetime
        import calendar
        
        now = datetime.now()
        year = int(request.args.get('year', now.year))
        month = int(request.args.get('month', now.month))
        cal = calendar.monthcalendar(year, month)
        
        return {
            'calendar': cal,
            'daily_sessions': {},
            'daily_status': {},
            'month': month,
            'year': year,
            'authenticated': False
        }
    
    from datetime import datetime, timedelta
    import calendar
    
    now = datetime.now()
    year = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))
    
    # Get month data
    cal = calendar.monthcalendar(year, month)
    
    # Get user's checkins for the month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Also get all checkins for current month without date filter as fallback
    all_response = db_service.checkin_table.query(
        KeyConditionExpression='username = :username',
        ExpressionAttributeValues={':username': session['username']}
    )
    all_checkins = all_response.get('Items', [])
    
    try:
        response = db_service.checkin_table.query(
            KeyConditionExpression='username = :username',
            FilterExpression='#date BETWEEN :start AND :end',
            ExpressionAttributeNames={'#date': 'date'},
            ExpressionAttributeValues={
                ':username': session['username'],
                ':start': start_date.isoformat(),
                ':end': end_date.isoformat()
            }
        )
        
        checkins = response.get('Items', [])

        from collections import defaultdict
        from datetime import time
        
        # Group check-ins by date - only successful ones with similarity >= 95%
        daily_checkins = defaultdict(list)
        for checkin in checkins:
            if checkin['status'] == 'success' and float(checkin.get('similarity', 0)) >= 95.0:
                date = checkin.get('date', checkin['checkin_time'][:10])
                daily_checkins[date].append(checkin)
        
        daily_sessions = {}
        daily_status = {}
        
        # Process each day with check-ins
        for date, day_checkins in daily_checkins.items():
            morning_checkin = None
            evening_checkin = None
            
            # Find valid check-ins for each session
            for checkin in day_checkins:
                session_type = checkin.get('session_type', 'other')
                checkin_time = datetime.fromisoformat(checkin['checkin_time']).time()
                
                # Assign to session based on session_type or time
                if session_type == 'morning' or (session_type == 'other' and time(6, 0) <= checkin_time <= time(14, 0)):
                    if not morning_checkin or checkin['checkin_time'] > morning_checkin['checkin_time']:
                        morning_checkin = checkin
                elif session_type == 'evening' or (session_type == 'other' and checkin_time > time(14, 0)):
                    if not evening_checkin or checkin['checkin_time'] > evening_checkin['checkin_time']:
                        evening_checkin = checkin
            
            # Build session data
            sessions = {'morning': None, 'evening': None}
            
            if morning_checkin:
                sessions['morning'] = {
                    'time': morning_checkin.get('time', morning_checkin['checkin_time'][11:19]),
                    'similarity': float(morning_checkin.get('similarity', 0)),
                    'status': morning_checkin['status'],
                    'session_type': morning_checkin.get('session_type', 'morning'),
                    'is_late': datetime.fromisoformat(morning_checkin['checkin_time']).time() > time(10, 0),
                    'completed': True
                }
            
            if evening_checkin:
                sessions['evening'] = {
                    'time': evening_checkin.get('time', evening_checkin['checkin_time'][11:19]),
                    'similarity': float(evening_checkin.get('similarity', 0)),
                    'status': evening_checkin['status'],
                    'session_type': evening_checkin.get('session_type', 'evening'),
                    'is_late': datetime.fromisoformat(evening_checkin['checkin_time']).time() > time(18, 0),
                    'completed': True
                }
            
            daily_sessions[date] = sessions
            
            # Determine daily status based on session completion
            if morning_checkin and evening_checkin:
                # Both sessions completed
                has_late = (sessions['morning']['is_late'] or sessions['evening']['is_late'])
                daily_status[date] = 'Late' if has_late else 'Complete'
            elif morning_checkin or evening_checkin:
                # Only one session completed
                is_late_session = (morning_checkin and sessions['morning']['is_late']) or (evening_checkin and sessions['evening']['is_late'])
                daily_status[date] = 'Late' if is_late_session else 'Partial'
        
        # Add days with no check-ins as 'No Data'
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str not in daily_status:
                daily_status[date_str] = 'No Data'
                daily_sessions[date_str] = {'morning': None, 'evening': None}
            current_date += timedelta(days=1)
        
    except Exception as e:
        daily_sessions = {}
    

    # Get monthly progress summary
    monthly_progress = db_service.get_monthly_progress(session['username'], year, month)
    
    return {
        'calendar': cal,
        'daily_sessions': daily_sessions,
        'daily_status': daily_status,
        'monthly_progress': monthly_progress,
        'month': month,
        'year': year,
        'authenticated': True
    }

@app.route('/export')
def export_history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    import csv
    from io import StringIO
    from flask import make_response
    
    # Get user's full history
    try:
        response = db_service.checkin_table.query(
            KeyConditionExpression='username = :username',
            ExpressionAttributeValues={':username': session['username']},
            ScanIndexForward=False
        )
        checkins = response.get('Items', [])
    except:
        checkins = []
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['Date', 'Time', 'Type', 'Similarity', 'Status'])
    
    # Data
    for checkin in checkins:
        writer.writerow([
            checkin['checkin_time'][:10],
            checkin['checkin_time'][11:19],
            checkin.get('check_type', 'other').title(),
            f"{float(checkin['similarity']):.1f}%",
            checkin['status'].title()
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=checkin-history-{session["username"]}.csv'
    
    return response

# Admin API Endpoints
@app.route('/api/admin/stats')
@admin_required
def api_admin_stats():
    from datetime import datetime
    
    all_users = db_service.get_all_users()
    all_checkins = db_service.get_all_checkins()
    today = datetime.now().date().isoformat()
    today_checkins = [c for c in all_checkins if c.get('date', c['checkin_time'][:10]) == today]
    
    return {
        'total_users': len([u for u in all_users if u.get('role') != 'admin']),
        'today_checkins': len(today_checkins),
        'success_rate': round((len([c for c in today_checkins if c['status'] == 'success']) / len(today_checkins) * 100) if today_checkins else 0, 1),
        'missed_checkins': len(all_users) - len(set(c['username'] for c in today_checkins)),
        'avg_similarity': round(sum(float(c.get('similarity', 0)) for c in today_checkins if c['status'] == 'success') / len([c for c in today_checkins if c['status'] == 'success']) if [c for c in today_checkins if c['status'] == 'success'] else 0, 1),
        'completion_rate': round((len(today_checkins) / len(all_users) * 100) if all_users else 0, 1)
    }

@app.route('/api/admin/sessions')
@admin_required
def api_admin_sessions():
    from datetime import datetime, time
    
    all_checkins = db_service.get_all_checkins()
    today = datetime.now().date().isoformat()
    today_checkins = [c for c in all_checkins if c.get('date', c['checkin_time'][:10]) == today]
    
    morning_sessions = []
    evening_sessions = []
    
    for checkin in today_checkins:
        if checkin['status'] == 'success':
            user = db_service.get_user(checkin['username'])
            if user:
                # Determine session type based on time if check_type is not set
                check_type = checkin.get('check_type')
                if not check_type or check_type == 'late':
                    checkin_time = datetime.fromisoformat(checkin['checkin_time']).time()
                    if time(6, 0) <= checkin_time <= time(14, 0):
                        check_type = 'morning'
                    else:
                        check_type = 'evening'
                
                # Determine status based on timing
                checkin_time = datetime.fromisoformat(checkin['checkin_time']).time()
                timing_status = 'on-time'
                if check_type == 'morning' and checkin_time > time(10, 0):
                    timing_status = 'late'
                elif check_type == 'evening' and checkin_time > time(18, 0):
                    timing_status = 'late'
                elif checkin.get('check_type') == 'late':
                    timing_status = 'late'
                
                session_data = {
                    'username': checkin['username'],
                    'full_name': user['full_name'],
                    'time': checkin.get('time', checkin['checkin_time'][11:19]),
                    'status': timing_status,
                    'similarity': round(float(checkin.get('similarity', 0)), 1)
                }
                
                if check_type == 'morning':
                    morning_sessions.append(session_data)
                elif check_type == 'evening':
                    evening_sessions.append(session_data)
    
    # Sort by time (most recent first)
    morning_sessions.sort(key=lambda x: x['time'], reverse=True)
    evening_sessions.sort(key=lambda x: x['time'], reverse=True)
    
    return {
        'morning': morning_sessions,
        'evening': evening_sessions
    }

@app.route('/api/admin/recent-activity')
@admin_required
def api_admin_recent_activity():
    all_checkins = db_service.get_all_checkins()[:20]  # Last 20 checkins
    
    activity = []
    for checkin in all_checkins:
        user = db_service.get_user(checkin['username'])
        if user:
            activity.append({
                'username': checkin['username'],
                'full_name': user['full_name'],
                'time': checkin.get('time', checkin['checkin_time'][11:19]),
                'check_type': checkin.get('check_type', 'other'),
                'status': checkin['status'],
                'similarity': round(float(checkin.get('similarity', 0)), 1)
            })
    
    return activity

@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    all_users = db_service.get_all_users()
    all_checkins = db_service.get_all_checkins()
    
    users_data = []
    for user in all_users:
        if user.get('role') != 'admin':
            user_checkins = [c for c in all_checkins if c['username'] == user['username']]
            last_checkin = max(user_checkins, key=lambda x: x['checkin_time'])['checkin_time'][:10] if user_checkins else None
            
            users_data.append({
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user.get('role', 'user'),
                'total_checkins': len(user_checkins),
                'last_checkin': last_checkin
            })
    
    return users_data

# Analytics API Endpoints
@app.route('/api/admin/analytics')
@admin_required
def api_admin_analytics():
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    all_checkins = db_service.get_all_checkins()
    
    # Get date range for last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)
    
    # Daily aggregation
    daily_counts = defaultdict(int)
    recent_checkins = []
    
    for checkin in all_checkins:
        checkin_date = datetime.fromisoformat(checkin['checkin_time']).date()
        if start_date <= checkin_date <= end_date:
            daily_counts[checkin_date.isoformat()] += 1
            recent_checkins.append(checkin)
    
    # Generate daily trend data
    trend_data = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        trend_data.append({
            'date': date_str,
            'count': daily_counts[date_str]
        })
        current_date += timedelta(days=1)
    
    # Calculate 7-day and 30-day insights
    last_7_days = [c for c in recent_checkins if (end_date - datetime.fromisoformat(c['checkin_time']).date()).days < 7]
    
    insights_7d = {
        'total_checkins': len(last_7_days),
        'on_time': len([c for c in last_7_days if c.get('check_type') in ['morning', 'evening'] and c['status'] == 'success']),
        'late': len([c for c in last_7_days if c.get('check_type') == 'late' and c['status'] == 'success']),
        'failed': len([c for c in last_7_days if c['status'] != 'success']),
        'avg_similarity': round(sum(float(c.get('similarity', 0)) for c in last_7_days if c['status'] == 'success') / len([c for c in last_7_days if c['status'] == 'success']) if [c for c in last_7_days if c['status'] == 'success'] else 0, 1),
        'success_rate': round(len([c for c in last_7_days if c['status'] == 'success']) / len(last_7_days) * 100 if last_7_days else 0, 1)
    }
    
    insights_30d = {
        'total_checkins': len(recent_checkins),
        'on_time': len([c for c in recent_checkins if c.get('check_type') in ['morning', 'evening'] and c['status'] == 'success']),
        'late': len([c for c in recent_checkins if c.get('check_type') == 'late' and c['status'] == 'success']),
        'failed': len([c for c in recent_checkins if c['status'] != 'success']),
        'avg_similarity': round(sum(float(c.get('similarity', 0)) for c in recent_checkins if c['status'] == 'success') / len([c for c in recent_checkins if c['status'] == 'success']) if [c for c in recent_checkins if c['status'] == 'success'] else 0, 1),
        'success_rate': round(len([c for c in recent_checkins if c['status'] == 'success']) / len(recent_checkins) * 100 if recent_checkins else 0, 1)
    }
    
    return {
        'trend_data': trend_data,
        'insights_7d': insights_7d,
        'insights_30d': insights_30d,
        'success_rate_data': {
            'success': len([c for c in recent_checkins if c['status'] == 'success']),
            'failed': len([c for c in recent_checkins if c['status'] != 'success'])
        }
    }

@app.route('/api/admin/export-checkins')
@admin_required
def api_admin_export_checkins():
    from datetime import datetime
    import csv
    from io import StringIO
    from flask import make_response
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    if not start_date or not end_date:
        return {'error': 'Start and end dates required'}, 400
    
    all_checkins = db_service.get_all_checkins()
    
    # Filter by date range
    filtered_checkins = []
    for checkin in all_checkins:
        checkin_date = checkin['checkin_time'][:10]
        if start_date <= checkin_date <= end_date:
            user = db_service.get_user(checkin['username'])
            if user:
                filtered_checkins.append({
                    'date': checkin_date,
                    'time': checkin['checkin_time'][11:19],
                    'username': checkin['username'],
                    'full_name': user['full_name'],
                    'check_type': checkin.get('check_type', 'other'),
                    'status': checkin['status'],
                    'similarity': float(checkin.get('similarity', 0))
                })
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['Date', 'Time', 'Username', 'Full Name', 'Type', 'Status', 'Similarity %'])
    
    # Data
    for checkin in filtered_checkins:
        writer.writerow([
            checkin['date'],
            checkin['time'],
            checkin['username'],
            checkin['full_name'],
            checkin['check_type'].title(),
            checkin['status'].title(),
            f"{checkin['similarity']:.1f}"
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=checkins-{start_date}-to-{end_date}.csv'
    
    return response

@app.route('/api/admin/export-users')
@admin_required
def api_admin_export_users():
    import csv
    from io import StringIO
    from flask import make_response
    
    all_users = db_service.get_all_users()
    all_checkins = db_service.get_all_checkins()
    
    # Calculate user statistics
    user_stats = []
    for user in all_users:
        if user.get('role') != 'admin':
            user_checkins = [c for c in all_checkins if c['username'] == user['username']]
            successful_checkins = [c for c in user_checkins if c['status'] == 'success']
            on_time_checkins = [c for c in successful_checkins if c.get('check_type') in ['morning', 'evening']]
            
            user_stats.append({
                'username': user['username'],
                'full_name': user['full_name'],
                'total_checkins': len(user_checkins),
                'successful_checkins': len(successful_checkins),
                'on_time_checkins': len(on_time_checkins),
                'on_time_percentage': round(len(on_time_checkins) / len(successful_checkins) * 100 if successful_checkins else 0, 1),
                'avg_similarity': round(sum(float(c.get('similarity', 0)) for c in successful_checkins) / len(successful_checkins) if successful_checkins else 0, 1),
                'last_checkin': max(user_checkins, key=lambda x: x['checkin_time'])['checkin_time'][:10] if user_checkins else 'Never'
            })
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['Username', 'Full Name', 'Total Check-ins', 'Successful', 'On-time %', 'Avg Similarity %', 'Last Check-in'])
    
    # Data
    for user in user_stats:
        writer.writerow([
            user['username'],
            user['full_name'],
            user['total_checkins'],
            user['successful_checkins'],
            user['on_time_percentage'],
            user['avg_similarity'],
            user['last_checkin']
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=user-statistics.csv'
    
    return response

@app.route('/admin/check-emails')
@admin_required
def admin_check_emails():
    """Check users without email addresses"""
    users_without_email = db_service.check_users_without_email()
    
    return {
        'users_without_email': users_without_email,
        'count': len(users_without_email),
        'message': f"Found {len(users_without_email)} users without email addresses"
    }

# Test endpoint disabled in production
# @app.route('/test-email')
# def test_email():
#     return {'error': 'Test endpoint disabled in production'}, 404

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email_or_username = request.form['email_or_username'].strip().lower()
        
        # Find user by email or username
        user = None
        if '@' in email_or_username:
            user = db_service.get_user_by_email(email_or_username)
        else:
            user = db_service.get_user(email_or_username)
        
        if not user or not user.get('email') or '@' not in user.get('email', ''):
            flash('Email address not found. Please contact your administrator.', 'error')
            return render_template('forgot_password.html')
        
        # Rate limiting check
        if 'forgot_password_attempts' not in session:
            session['forgot_password_attempts'] = []
        
        now = datetime.now().timestamp()
        # Remove attempts older than 1 hour
        session['forgot_password_attempts'] = [t for t in session['forgot_password_attempts'] if now - t < 3600]
        
        if len(session['forgot_password_attempts']) >= 5:
            flash('Too many attempts. Please try again later.', 'error')
            return render_template('forgot_password.html')
        
        # Check if OTP was sent recently (60 seconds)
        if session['forgot_password_attempts'] and now - session['forgot_password_attempts'][-1] < 60:
            flash('Please wait 60 seconds before requesting another code.', 'warning')
            return render_template('forgot_password.html')
        
        # Generate OTP
        otp = email_service.generate_otp()
        success, error_message = email_service.send_otp_email(user['email'], otp, user['full_name'])
        
        if success:
            # Store OTP data in session
            session['password_reset'] = {
                'username': user['username'],
                'email': user['email'],
                'otp': otp,
                'timestamp': now,
                'attempts': 0
            }
            session['forgot_password_attempts'].append(now)
            
            flash(f'Verification code sent to {user["email"]}', 'success')
            return redirect(url_for('verify_reset_otp'))
        else:
            flash(f'Failed to send verification code: {error_message}', 'error')
    
    return render_template('forgot_password.html')

@app.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    if 'password_reset' not in session:
        flash('Please start the password reset process first.', 'error')
        return redirect(url_for('forgot_password'))
    
    reset_data = session['password_reset']
    
    # Check if OTP expired (5 minutes)
    if datetime.now().timestamp() - reset_data['timestamp'] > 300:
        session.pop('password_reset', None)
        flash('Verification code expired. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        entered_otp = request.form['otp'].strip()
        
        # Increment attempts
        reset_data['attempts'] += 1
        session['password_reset'] = reset_data
        
        if reset_data['attempts'] > 5:
            session.pop('password_reset', None)
            flash('Too many incorrect attempts. Please start over.', 'error')
            return redirect(url_for('forgot_password'))
        
        if entered_otp == reset_data['otp']:
            # OTP verified, proceed to password reset
            session['password_reset']['verified'] = True
            return redirect(url_for('reset_password'))
        else:
            flash(f'Invalid verification code. {6 - reset_data["attempts"]} attempts remaining.', 'error')
    
    return render_template('verify_reset_otp.html', email=reset_data['email'])

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'password_reset' not in session or not session['password_reset'].get('verified'):
        flash('Please complete the verification process first.', 'error')
        return redirect(url_for('forgot_password'))
    
    reset_data = session['password_reset']
    
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('reset_password.html')
        
        # Update password in database
        try:
            db_service.users_table.update_item(
                Key={'username': reset_data['username']},
                UpdateExpression='SET password = :pwd',
                ExpressionAttributeValues={':pwd': new_password}
            )
            
            # Clear session data
            session.pop('password_reset', None)
            session.pop('forgot_password_attempts', None)
            
            flash('Password updated successfully! You can now sign in with your new password.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Failed to update password. Please try again.', 'error')
    
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Health check endpoint for AWS
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'fcj-checkin'}

# Lambda handler for Zappa deployment
def lambda_handler(event, context):
    return app(event, context)

# Initialize AWS resources
def init_aws_resources():
    """Initialize AWS resources on startup"""
    try:
        db_service.create_tables()
        settings_service.create_settings_table()
        return True
    except Exception as e:
        print(f"AWS initialization error: {e}")
        return False

# Admin Settings Routes
@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        try:
            # Parse form data safely
            settings_data = {
                'morning_start': request.form.get('morning_start', '08:30').strip(),
                'morning_end': request.form.get('morning_end', '10:00').strip(),
                'evening_start': request.form.get('evening_start', '16:30').strip(),
                'evening_end': request.form.get('evening_end', '18:00').strip(),
                'similarity_threshold': float(request.form.get('similarity_threshold', 95)),
                'allow_late_checkin': 'allow_late_checkin' in request.form,
                'prevent_duplicate_checkin': 'prevent_duplicate_checkin' in request.form
            }
            
            # Validate settings
            errors = settings_service.validate_settings(settings_data)
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('admin_settings.html', settings=settings_service.get_settings())
            
            # Save settings
            if settings_service.update_settings(settings_data):
                flash('Settings updated successfully!', 'success')
            else:
                flash('Failed to update settings', 'error')
                
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
        except Exception as e:
            flash('Failed to update settings', 'error')
    
    settings = settings_service.get_settings()
    return render_template('admin_settings.html', settings=settings)

@app.route('/admin/save_settings', methods=['POST'])
@admin_required
def admin_save_settings():
    try:
        data = request.get_json() if request.is_json else request.form
        
        settings = {
            'morning_start': data.get('morning_start', '08:30').strip(),
            'morning_end': data.get('morning_end', '10:00').strip(),
            'evening_start': data.get('evening_start', '16:30').strip(),
            'evening_end': data.get('evening_end', '18:00').strip(),
            'similarity_threshold': float(data.get('similarity_threshold', 95)),
            'allow_late_checkin': bool(data.get('allow_late_checkin', False)),
            'prevent_duplicate_checkin': bool(data.get('prevent_duplicate_checkin', True))
        }
        
        # Validate inputs
        errors = settings_service.validate_settings(settings)
        if errors:
            return {'success': False, 'errors': errors}, 400
        
        # Save settings
        if settings_service.update_settings(settings):
            return {'success': True, 'message': 'Settings updated successfully'}
        else:
            return {'success': False, 'error': 'Failed to save settings'}, 500
            
    except ValueError as e:
        return {'success': False, 'error': f'Invalid input: {str(e)}'}, 400
    except Exception as e:
        return {'success': False, 'error': 'Server error occurred'}, 500

@app.route('/api/admin/settings')
@admin_required
def api_admin_settings():
    try:
        return {'success': True, 'settings': settings_service.get_settings()}
    except Exception as e:
        return {'success': False, 'error': 'Failed to load settings'}, 500

if __name__ == '__main__':
    # Initialize AWS resources
    init_aws_resources()
    
    # Run application locally
    app.run(host='0.0.0.0', port=5000, debug=False)