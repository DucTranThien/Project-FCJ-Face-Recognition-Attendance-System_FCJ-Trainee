import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError
from services.settings_service import SettingsService

class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'ap-southeast-1'))
        self.users_table = self.dynamodb.Table(os.getenv('USERS_TABLE'))
        self.checkin_table = self.dynamodb.Table(os.getenv('CHECKIN_TABLE'))
        self.settings_service = SettingsService()
    
    def create_tables(self):
        try:
            # Create Users table
            self.dynamodb.create_table(
                TableName=os.getenv('USERS_TABLE'),
                KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Create CheckInHistory table
            self.dynamodb.create_table(
                TableName=os.getenv('CHECKIN_TABLE'),
                KeySchema=[
                    {'AttributeName': 'username', 'KeyType': 'HASH'},
                    {'AttributeName': 'checkin_time', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'username', 'AttributeType': 'S'},
                    {'AttributeName': 'checkin_time', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                pass
    
    def create_user(self, username, full_name, password, image_url, email=None, role=None):
        try:
            # Set role based on username or default to 'user'
            if role is None:
                role = 'admin' if username == 'admin' else 'user'
            
            self.users_table.put_item(
                Item={
                    'username': username,
                    'full_name': full_name,
                    'password': password,
                    'image_url': image_url,
                    'email': email or '',
                    'role': role,
                    'created_at': datetime.now().isoformat()
                }
            )
            return True
        except ClientError:
            return False
    
    def get_user(self, username):
        try:
            response = self.users_table.get_item(Key={'username': username})
            return response.get('Item')
        except ClientError:
            return None
    
    def save_checkin(self, username, similarity, status):
        try:
            from datetime import datetime, time
            now = datetime.now()
            current_time = now.time()
            
            # Get dynamic similarity threshold
            threshold = self.settings_service.get_similarity_threshold()
            
            # Only save if similarity meets threshold and status is success
            if status != 'success' or similarity < threshold:
                return {
                    'error': 'recognition_failed',
                    'similarity': similarity,
                    'threshold': threshold,
                    'message': f'Face recognition failed. Similarity: {similarity:.1f}% (Required: ≥95%)',
                    'can_retry': True,
                    'session_type': 'unknown'
                }
            
            # Get dynamic time windows
            time_windows = self.settings_service.get_time_windows()
            morning_start = time.fromisoformat(time_windows['morning']['start'])
            morning_end = time.fromisoformat(time_windows['morning']['end'])
            evening_start = time.fromisoformat(time_windows['evening']['start'])
            evening_end = time.fromisoformat(time_windows['evening']['end'])
            
            # Determine session and punctuality
            if morning_start <= current_time <= morning_end:
                session_type = 'morning'
                check_type = 'morning'
            elif evening_start <= current_time <= evening_end:
                session_type = 'evening'
                check_type = 'evening'
            else:
                session_type = 'other'
                check_type = 'late'
            
            # Check for existing successful check-in for this session today
            today = now.date().isoformat()
            existing = self.checkin_table.query(
                KeyConditionExpression='username = :username',
                FilterExpression='#date = :date AND session_type = :session AND #status = :success',
                ExpressionAttributeNames={'#date': 'date', '#status': 'status'},
                ExpressionAttributeValues={
                    ':username': username,
                    ':date': today,
                    ':session': session_type,
                    ':success': 'success'
                }
            )
            
            if existing.get('Items'):
                return {
                    'error': 'duplicate',
                    'session_type': session_type,
                    'message': f'You have already completed {session_type} check-in today'
                }
            
            # Save successful check-in
            self.checkin_table.put_item(
                Item={
                    'username': username,
                    'checkin_time': now.isoformat(),
                    'date': today,
                    'time': current_time.strftime('%H:%M:%S'),
                    'session_type': session_type,
                    'check_type': check_type,
                    'checkin_status': 'completed',
                    'similarity': str(similarity),
                    'status': status
                }
            )
            
            return {
                'status': 'success',
                'session_type': session_type,
                'check_type': check_type,
                'time': current_time.strftime('%H:%M:%S'),
                'date': today,
                'similarity': similarity,
                'message': f'{session_type.title()} check-in completed successfully'
            }
        except ClientError as e:
            return {
                'error': 'database_error',
                'message': 'Database error occurred during check-in',
                'session_type': 'unknown'
            }
        except Exception as e:
            return {
                'error': 'system_error',
                'message': 'System error occurred during check-in',
                'session_type': 'unknown'
            }
    
    def get_all_checkins(self):
        try:
            response = self.checkin_table.scan()
            return sorted(response.get('Items', []), key=lambda x: x['checkin_time'], reverse=True)
        except ClientError:
            return []
    
    def get_checkin_statistics(self, days=7):
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict
            
            # Get all checkins
            checkins = self.get_all_checkins()
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # Group checkins by date
            daily_counts = defaultdict(int)
            
            for checkin in checkins:
                checkin_date = datetime.fromisoformat(checkin['checkin_time']).date()
                if start_date <= checkin_date <= end_date:
                    daily_counts[checkin_date.isoformat()] += 1
            
            # Fill missing dates with 0
            result = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.isoformat()
                result.append({
                    'date': date_str,
                    'count': daily_counts[date_str]
                })
                current_date += timedelta(days=1)
            
            return result
        except Exception:
            return []
    
    def get_today_checkin(self, username):
        """Check if user has checked in today"""
        try:
            from datetime import datetime
            today = datetime.now().date().isoformat()
            
            response = self.checkin_table.query(
                KeyConditionExpression='username = :username',
                FilterExpression='begins_with(checkin_time, :today)',
                ExpressionAttributeValues={
                    ':username': username,
                    ':today': today
                },
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception:
            return None
    
    def get_user_checkin_summary(self, username, days=30):
        """Get user's check-in summary for dashboard"""
        try:
            from datetime import datetime, timedelta
            from collections import defaultdict
            
            # Get user's checkins
            response = self.checkin_table.query(
                KeyConditionExpression='username = :username',
                ExpressionAttributeValues={':username': username},
                ScanIndexForward=False
            )
            
            checkins = response.get('Items', [])
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # Process checkins
            daily_checkins = defaultdict(list)
            total_checkins = 0
            successful_checkins = 0
            
            for checkin in checkins:
                checkin_date = datetime.fromisoformat(checkin['checkin_time']).date()
                if checkin_date >= start_date:
                    daily_checkins[checkin_date.isoformat()].append(checkin)
                    total_checkins += 1
                    if checkin['status'] == 'success':
                        successful_checkins += 1
            
            # Calculate streak
            streak = 0
            current_date = end_date
            while current_date >= start_date:
                if current_date.isoformat() in daily_checkins:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            
            # Recent checkins (last 5)
            recent_checkins = sorted(checkins[:5], key=lambda x: x['checkin_time'], reverse=True)
            
            return {
                'total_checkins': total_checkins,
                'successful_checkins': successful_checkins,
                'streak': streak,
                'recent_checkins': recent_checkins,
                'daily_checkins': dict(daily_checkins)
            }
        except Exception:
            return {
                'total_checkins': 0,
                'successful_checkins': 0,
                'streak': 0,
                'recent_checkins': [],
                'daily_checkins': {}
            }
    
    def get_today_sessions(self, username):
        """Get today's morning and evening check-ins with enhanced status"""
        try:
            from datetime import datetime, time
            today = datetime.now().date().isoformat()
            
            response = self.checkin_table.query(
                KeyConditionExpression='username = :username',
                FilterExpression='#date = :today AND #status = :success',
                ExpressionAttributeNames={'#date': 'date', '#status': 'status'},
                ExpressionAttributeValues={
                    ':username': username,
                    ':today': today,
                    ':success': 'success'
                }
            )
            
            sessions = {'morning': None, 'evening': None}
            for item in response.get('Items', []):
                session_type = item.get('session_type', 'other')
                
                # Only count successful check-ins with similarity >= 95%
                if item['status'] == 'success' and float(item.get('similarity', 0)) >= 95.0:
                    checkin_time = datetime.fromisoformat(item['checkin_time']).time()
                    
                    # Determine if on time or late based on session windows
                    is_late = False
                    if session_type == 'morning' and checkin_time > time(10, 0):
                        is_late = True
                    elif session_type == 'evening' and checkin_time > time(18, 0):
                        is_late = True
                    elif session_type == 'other':
                        is_late = True
                    
                    if session_type in ['morning', 'evening']:
                        sessions[session_type] = {
                            'checkin_time': item['checkin_time'],
                            'time': item.get('time', item['checkin_time'][11:19]),
                            'status': item['status'],
                            'similarity': float(item.get('similarity', 0)),
                            'check_type': item.get('check_type', session_type),
                            'is_late': is_late,
                            'completed': True
                        }
                    elif session_type == 'other':
                        # Assign late check-ins to appropriate session
                        if time(6, 0) <= checkin_time <= time(14, 0):
                            target_session = 'morning'
                        else:
                            target_session = 'evening'
                        
                        sessions[target_session] = {
                            'checkin_time': item['checkin_time'],
                            'time': item.get('time', item['checkin_time'][11:19]),
                            'status': item['status'],
                            'similarity': float(item.get('similarity', 0)),
                            'check_type': 'late',
                            'is_late': True,
                            'completed': True
                        }
            
            return sessions
        except Exception:
            return {'morning': None, 'evening': None}
    
    def get_leaderboard_data(self):
        """Get leaderboard data for all users with accurate attendance calculation"""
        try:
            from collections import defaultdict
            from datetime import datetime, timedelta, time
            
            # Get all users
            users_response = self.users_table.scan()
            users = {u['username']: u for u in users_response.get('Items', [])}
            
            # Get all checkins
            checkins_response = self.checkin_table.scan()
            checkins = checkins_response.get('Items', [])
            
            leaderboard = []
            
            for username, user_data in users.items():
                if user_data.get('role') == 'admin':
                    continue
                
                # Only count successful checkins with similarity >= 95%
                user_checkins = [c for c in checkins if c['username'] == username and c['status'] == 'success' and float(c.get('similarity', 0)) >= 95.0]
                
                # Group checkins by date
                daily_checkins = defaultdict(list)
                for checkin in user_checkins:
                    date = checkin.get('date', checkin['checkin_time'][:10])
                    daily_checkins[date].append(checkin)
                
                # Calculate daily status - only count as complete if both morning and evening are done
                complete_days = 0
                for date, day_checkins in daily_checkins.items():
                    morning_checkin = None
                    evening_checkin = None
                    
                    for checkin in day_checkins:
                        checkin_time = datetime.fromisoformat(checkin['checkin_time']).time()
                        
                        # Determine session based on time and check_type
                        if checkin.get('check_type') == 'morning' or (time(6, 0) <= checkin_time <= time(14, 0)):
                            if not morning_checkin or checkin['checkin_time'] > morning_checkin['checkin_time']:
                                morning_checkin = checkin
                        elif checkin.get('check_type') == 'evening' or checkin_time > time(14, 0):
                            if not evening_checkin or checkin['checkin_time'] > evening_checkin['checkin_time']:
                                evening_checkin = checkin
                    
                    # Count as complete day only if both sessions are done
                    if morning_checkin and evening_checkin:
                        complete_days += 1
                
                # Calculate current streak (consecutive complete days from today backwards)
                current_streak = 0
                current_date = datetime.now().date()
                
                while current_date >= datetime.now().date() - timedelta(days=365):  # Limit to 1 year
                    date_str = current_date.isoformat()
                    day_checkins = daily_checkins.get(date_str, [])
                    
                    # Check if this day has both morning and evening checkins
                    has_morning = any(c for c in day_checkins if datetime.fromisoformat(c['checkin_time']).time() <= time(14, 0))
                    has_evening = any(c for c in day_checkins if datetime.fromisoformat(c['checkin_time']).time() > time(14, 0))
                    
                    if has_morning and has_evening:
                        current_streak += 1
                        current_date -= timedelta(days=1)
                    else:
                        break
                
                # Calculate highest streak
                highest_streak = 0
                temp_streak = 0
                sorted_dates = sorted(daily_checkins.keys())
                
                for date in sorted_dates:
                    day_checkins = daily_checkins[date]
                    has_morning = any(c for c in day_checkins if datetime.fromisoformat(c['checkin_time']).time() <= time(14, 0))
                    has_evening = any(c for c in day_checkins if datetime.fromisoformat(c['checkin_time']).time() > time(14, 0))
                    
                    if has_morning and has_evening:
                        temp_streak += 1
                        highest_streak = max(highest_streak, temp_streak)
                    else:
                        temp_streak = 0
                
                # Total checkins count
                total_checkins = len(user_checkins)
                
                # Determine badge based on complete days
                if complete_days >= 30:
                    badge = {'name': 'Champion', 'icon': '🏆', 'class': 'warning'}
                elif complete_days >= 10:
                    badge = {'name': 'Star', 'icon': '⭐', 'class': 'success'}
                elif complete_days >= 5:
                    badge = {'name': 'Rising', 'icon': '🌟', 'class': 'info'}
                else:
                    badge = {'name': 'Starter', 'icon': '🌱', 'class': 'light text-dark'}
                
                leaderboard.append({
                    'username': username,
                    'full_name': user_data.get('full_name', username),
                    'complete_days': complete_days,
                    'current_streak': current_streak,
                    'highest_streak': highest_streak,
                    'total_checkins': total_checkins,
                    'badge': badge,
                    'image_url': user_data.get('image_url', '')
                })
            
            # Sort by complete days (desc), then current streak (desc), then total checkins (desc)
            return sorted(leaderboard, key=lambda x: (x['complete_days'], x['current_streak'], x['total_checkins']), reverse=True)
            
        except Exception as e:
            print(f"Leaderboard error: {e}")
            return []
    
    def update_user_role(self, username, role):
        """Update user role - helper for migration"""
        try:
            self.users_table.update_item(
                Key={'username': username},
                UpdateExpression='SET #role = :role',
                ExpressionAttributeNames={'#role': 'role'},
                ExpressionAttributeValues={':role': role}
            )
            return True
        except ClientError:
            return False
    
    def get_all_users(self):
        """Get all users - helper for migration"""
        try:
            response = self.users_table.scan()
            return response.get('Items', [])
        except ClientError:
            return []
    
    def get_user_by_email(self, email):
        """Get user by email address"""
        try:
            response = self.users_table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': email.lower()}
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError:
            return None
    
    def get_user_attendance_summary(self, username):
        """Get detailed attendance summary for a specific user"""
        try:
            from collections import defaultdict
            from datetime import datetime, time
            
            # Get user's checkins
            response = self.checkin_table.query(
                KeyConditionExpression='username = :username',
                ExpressionAttributeValues={':username': username}
            )
            
            user_checkins = [c for c in response.get('Items', []) if c['status'] == 'success']
            
            # Group by date
            daily_checkins = defaultdict(list)
            for checkin in user_checkins:
                date = checkin.get('date', checkin['checkin_time'][:10])
                daily_checkins[date].append(checkin)
            
            # Calculate daily status
            daily_status = {}
            for date, day_checkins in daily_checkins.items():
                morning_checkin = None
                evening_checkin = None
                has_late = False
                
                for checkin in day_checkins:
                    session_type = checkin.get('session_type', checkin.get('check_type', 'other'))  # Fallback for old records
                    punctuality = checkin.get('check_type', 'on_time')  # New punctuality field
                    checkin_time = datetime.fromisoformat(checkin['checkin_time']).time()
                    
                    if session_type == 'morning' or (session_type == 'other' and time(6, 0) <= checkin_time <= time(14, 0)):
                        morning_checkin = checkin
                        if punctuality == 'late':
                            has_late = True
                    elif session_type == 'evening' or (session_type == 'other' and checkin_time > time(14, 0)):
                        evening_checkin = checkin
                        if punctuality == 'late':
                            has_late = True
                
                if morning_checkin and evening_checkin:
                    daily_status[date] = 'Late' if has_late else 'Complete'
                elif morning_checkin or evening_checkin:
                    daily_status[date] = 'Late' if has_late else 'Partial'
            
            return {
                'daily_status': daily_status,
                'total_checkins': len(user_checkins),
                'complete_days': sum(1 for status in daily_status.values() if status == 'Complete')
            }
            
        except Exception:
            return {'daily_status': {}, 'total_checkins': 0, 'complete_days': 0}
    
    def can_checkin_now(self, username):
        """Check if user can check-in now based on session windows and existing check-ins"""
        try:
            from datetime import datetime, time
            now = datetime.now()
            current_time = now.time()
            
            # Get dynamic time windows
            time_windows = self.settings_service.get_time_windows()
            morning_start = time.fromisoformat(time_windows['morning']['start'])
            morning_end = time.fromisoformat(time_windows['morning']['end'])
            evening_start = time.fromisoformat(time_windows['evening']['start'])
            evening_end = time.fromisoformat(time_windows['evening']['end'])
            
            # Check current session window
            if morning_start <= current_time <= morning_end:
                session_type = 'morning'
                window_end = time_windows['morning']['end']
            elif evening_start <= current_time <= evening_end:
                session_type = 'evening'
                window_end = time_windows['evening']['end']
            else:
                # Check if late check-in is allowed
                if self.settings_service.is_late_checkin_allowed():
                    session_type = 'other'
                    window_end = 'Late check-in allowed'
                else:
                    return {
                        'can_checkin': False,
                        'reason': 'outside_window',
                        'message': f'Check-in only allowed during: Morning ({time_windows["morning"]["start"]}-{time_windows["morning"]["end"]}) or Evening ({time_windows["evening"]["start"]}-{time_windows["evening"]["end"]})'
                    }
            
            # Check if already checked in for this session today
            today_sessions = self.get_today_sessions(username)
            if today_sessions.get(session_type):
                return {
                    'can_checkin': False,
                    'reason': 'already_completed',
                    'session_type': session_type,
                    'message': f'{session_type.title()} check-in already completed today'
                }
            
            return {
                'can_checkin': True,
                'session_type': session_type,
                'window_end': window_end
            }
            
        except Exception:
            return {
                'can_checkin': False,
                'reason': 'error',
                'message': 'Unable to verify check-in status'
            }
    
    def check_users_without_email(self):
        """Check and report users without email addresses"""
        try:
            all_users = self.get_all_users()
            users_without_email = []
            
            for user in all_users:
                email = user.get('email', '').strip()
                if not email or '@' not in email:
                    users_without_email.append({
                        'username': user['username'],
                        'full_name': user.get('full_name', 'N/A'),
                        'role': user.get('role', 'user'),
                        'email': email or 'None'
                    })
            
            return users_without_email
        except Exception:
            return []
    
    def get_monthly_progress(self, username, year, month):
        """Get monthly progress summary with accurate completion data"""
        try:
            from datetime import datetime, timedelta, time
            from collections import defaultdict
            import calendar
            
            # Get month boundaries
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            # Get total days in month
            total_days = calendar.monthrange(year, month)[1]
            
            # Get user's successful check-ins for the month
            response = self.checkin_table.query(
                KeyConditionExpression='username = :username',
                FilterExpression='#date BETWEEN :start AND :end AND #status = :success',
                ExpressionAttributeNames={'#date': 'date', '#status': 'status'},
                ExpressionAttributeValues={
                    ':username': username,
                    ':start': start_date.isoformat(),
                    ':end': end_date.isoformat(),
                    ':success': 'success'
                }
            )
            
            checkins = [c for c in response.get('Items', []) if float(c.get('similarity', 0)) >= 95.0]
            
            # Group by date
            daily_checkins = defaultdict(list)
            for checkin in checkins:
                date = checkin.get('date', checkin['checkin_time'][:10])
                daily_checkins[date].append(checkin)
            
            # Calculate complete days
            complete_days = 0
            for date, day_checkins in daily_checkins.items():
                morning_checkin = None
                evening_checkin = None
                
                for checkin in day_checkins:
                    session_type = checkin.get('session_type', 'other')
                    checkin_time = datetime.fromisoformat(checkin['checkin_time']).time()
                    
                    if session_type == 'morning' or (session_type == 'other' and time(6, 0) <= checkin_time <= time(14, 0)):
                        if not morning_checkin or checkin['checkin_time'] > morning_checkin['checkin_time']:
                            morning_checkin = checkin
                    elif session_type == 'evening' or (session_type == 'other' and checkin_time > time(14, 0)):
                        if not evening_checkin or checkin['checkin_time'] > evening_checkin['checkin_time']:
                            evening_checkin = checkin
                
                # Count as complete day only if both sessions are done
                if morning_checkin and evening_checkin:
                    complete_days += 1
            
            # Calculate percentage
            completion_percentage = round((complete_days / total_days) * 100, 1) if total_days > 0 else 0
            
            return {
                'complete_days': complete_days,
                'total_days': total_days,
                'completion_percentage': completion_percentage,
                'month': month,
                'year': year
            }
            
        except Exception as e:
            return {
                'complete_days': 0,
                'total_days': 0,
                'completion_percentage': 0,
                'month': month,
                'year': year
            }