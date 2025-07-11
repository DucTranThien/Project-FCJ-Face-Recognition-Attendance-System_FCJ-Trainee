import boto3
import os
import json
from datetime import time
from botocore.exceptions import ClientError

class SettingsService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'ap-southeast-1'))
        self.settings_table = self.dynamodb.Table(os.getenv('SETTINGS_TABLE', 'fcj-checkin-settings'))
        self._default_settings = {
            'morning_start': '08:30',
            'morning_end': '10:00',
            'evening_start': '16:30',
            'evening_end': '18:00',
            'similarity_threshold': 95.0,
            'allow_late_checkin': True,
            'prevent_duplicate_checkin': True
        }
    
    def create_settings_table(self):
        """Create settings table if it doesn't exist"""
        try:
            self.dynamodb.create_table(
                TableName=os.getenv('SETTINGS_TABLE', 'fcj-checkin-settings'),
                KeySchema=[{'AttributeName': 'setting_key', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'setting_key', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                pass
    
    def get_settings(self):
        """Get all system settings"""
        try:
            response = self.settings_table.scan()
            settings = {}
            
            # Convert DynamoDB items to dict
            for item in response.get('Items', []):
                settings[item['setting_key']] = item['setting_value']
            
            # Merge with defaults for missing keys
            for key, default_value in self._default_settings.items():
                if key not in settings:
                    settings[key] = default_value
            
            return settings
        except Exception:
            # Fallback to JSON file for local development
            return self._load_from_json()
    
    def update_setting(self, key, value):
        """Update a single setting"""
        try:
            self.settings_table.put_item(
                Item={
                    'setting_key': key,
                    'setting_value': value
                }
            )
            return True
        except Exception:
            return False
    
    def update_settings(self, settings_dict):
        """Update multiple settings"""
        try:
            for key, value in settings_dict.items():
                self.settings_table.put_item(
                    Item={
                        'setting_key': key,
                        'setting_value': value
                    }
                )
            return True
        except Exception:
            # Fallback to JSON file for local development
            return self._save_to_json(settings_dict)
    
    def get_time_windows(self):
        """Get check-in time windows"""
        settings = self.get_settings()
        return {
            'morning': {
                'start': settings['morning_start'],
                'end': settings['morning_end']
            },
            'evening': {
                'start': settings['evening_start'],
                'end': settings['evening_end']
            }
        }
    
    def get_similarity_threshold(self):
        """Get similarity threshold"""
        settings = self.get_settings()
        return float(settings['similarity_threshold'])
    
    def is_late_checkin_allowed(self):
        """Check if late check-in is allowed"""
        settings = self.get_settings()
        return bool(settings['allow_late_checkin'])
    
    def is_duplicate_prevention_enabled(self):
        """Check if duplicate prevention is enabled"""
        settings = self.get_settings()
        return bool(settings['prevent_duplicate_checkin'])
    
    def validate_time_format(self, time_str):
        """Validate time format HH:MM"""
        try:
            if not time_str or not isinstance(time_str, str):
                return False
            time.fromisoformat(time_str.strip())
            return True
        except (ValueError, AttributeError):
            return False
    
    def validate_settings(self, settings_dict):
        """Validate settings before saving"""
        errors = []
        
        # Validate time formats
        time_fields = ['morning_start', 'morning_end', 'evening_start', 'evening_end']
        for field in time_fields:
            if field in settings_dict:
                value = settings_dict[field]
                if not value or not self.validate_time_format(value):
                    errors.append(f"Invalid time format for {field.replace('_', ' ').title()}")
        
        # Validate similarity threshold
        if 'similarity_threshold' in settings_dict:
            try:
                threshold = float(settings_dict['similarity_threshold'])
                if threshold < 80 or threshold > 100:
                    errors.append("Similarity threshold must be between 80 and 100")
            except (ValueError, TypeError):
                errors.append("Invalid similarity threshold value")
        
        # Validate time ranges
        try:
            if all(field in settings_dict and settings_dict[field] for field in ['morning_start', 'morning_end']):
                morning_start = time.fromisoformat(settings_dict['morning_start'])
                morning_end = time.fromisoformat(settings_dict['morning_end'])
                if morning_start >= morning_end:
                    errors.append("Morning start time must be before end time")
            
            if all(field in settings_dict and settings_dict[field] for field in ['evening_start', 'evening_end']):
                evening_start = time.fromisoformat(settings_dict['evening_start'])
                evening_end = time.fromisoformat(settings_dict['evening_end'])
                if evening_start >= evening_end:
                    errors.append("Evening start time must be before end time")
        except ValueError:
            errors.append("Invalid time format detected")
        
        return errors
    
    def _load_from_json(self):
        """Load settings from JSON file (fallback)"""
        try:
            settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults
                for key, default_value in self._default_settings.items():
                    if key not in settings:
                        settings[key] = default_value
                return settings
        except Exception:
            pass
        return self._default_settings.copy()
    
    def _save_to_json(self, settings_dict):
        """Save settings to JSON file (fallback)"""
        try:
            settings_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings.json')
            
            # Load existing settings
            current_settings = self._load_from_json()
            
            # Update with new values
            current_settings.update(settings_dict)
            
            # Save to file
            with open(settings_file, 'w') as f:
                json.dump(current_settings, f, indent=4)
            
            return True
        except Exception:
            return False