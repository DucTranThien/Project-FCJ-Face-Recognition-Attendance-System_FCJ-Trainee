import smtplib
import os
import random
import string
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        # Clean up App Password (remove spaces)
        raw_password = os.getenv('SMTP_PASSWORD')
        self.smtp_password = raw_password.replace(' ', '') if raw_password else None
        self.from_email = os.getenv('FROM_EMAIL') or self.smtp_username
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def _validate_config(self):
        """Validate SMTP configuration with Gmail-specific checks"""
        missing = []
        warnings = []
        
        if not self.smtp_username:
            missing.append('SMTP_USERNAME')
        elif not '@gmail.com' in self.smtp_username.lower() and self.smtp_server == 'smtp.gmail.com':
            warnings.append('Username should be a Gmail address for Gmail SMTP')
        
        if not self.smtp_password or self.smtp_password.strip() == '':
            missing.append('SMTP_PASSWORD')
        elif len(self.smtp_password) != 16 and self.smtp_server == 'smtp.gmail.com':
            warnings.append(f'Gmail App Password should be 16 characters (current: {len(self.smtp_password)})')
        
        if not self.from_email:
            missing.append('FROM_EMAIL')
        elif not '@gmail.com' in self.from_email.lower() and self.smtp_server == 'smtp.gmail.com':
            warnings.append('FROM_EMAIL should be a Gmail address for Gmail SMTP')
        
        return len(missing) == 0
    
    def send_otp_email(self, to_email, otp, username, retry_count=2):
        """Send OTP via email with retry logic"""
        # Validate inputs
        if not to_email or '@' not in to_email:
            return False, "Invalid email address"
        
        if not self._validate_config():
            return False, "SMTP configuration incomplete"
        
        for attempt in range(retry_count):
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['From'] = self.from_email
                msg['To'] = to_email
                msg['Subject'] = "FCJ Check-in - Login Verification Code"
                
                # HTML body
                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                        <h2 style="color: #007bff; text-align: center;">FCJ Face Check-in System</h2>
                        <p>Hello <strong>{username}</strong>,</p>
                        <p>Your login verification code is:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <h1 style="color: #007bff; font-size: 36px; letter-spacing: 8px; background: white; padding: 20px; border-radius: 8px; display: inline-block;">{otp}</h1>
                        </div>
                        <p style="color: #dc3545;"><strong>This code will expire in 5 minutes.</strong></p>
                        <p>If you didn't request this code, please ignore this email.</p>
                        <hr style="margin: 30px 0;">
                        <p style="color: #6c757d; font-size: 14px;">Best regards,<br>FCJ Check-in Team</p>
                    </div>
                </body>
                </html>
                """
                
                # Text fallback
                text_body = f"""
                FCJ Face Check-in System
                
                Hello {username},
                
                Your login verification code is: {otp}
                
                This code will expire in 5 minutes.
                
                If you didn't request this code, please ignore this email.
                
                Best regards,
                FCJ Check-in Team
                """
                
                msg.attach(MIMEText(text_body, 'plain'))
                msg.attach(MIMEText(html_body, 'html'))
                
                # Connect and send with 10-second timeout
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                server.set_debuglevel(0)
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                server.quit()
                
                return True, "Email sent successfully"
                
            except smtplib.SMTPAuthenticationError as e:
                if 'Application-specific password required' in str(e) or 'Username and Password not accepted' in str(e):
                    return False, "Gmail requires App Password - enable 2FA and generate App Password"
                return False, "SMTP authentication failed - check username/password"
                
            except smtplib.SMTPRecipientsRefused as e:
                return False, "Invalid recipient email address"
                
            except smtplib.SMTPServerDisconnected as e:
                if attempt < retry_count - 1:
                    continue
                return False, "SMTP server connection failed"
                
            except socket.timeout as e:
                if attempt < retry_count - 1:
                    continue
                return False, "SMTP connection timeout"
                
            except socket.gaierror as e:
                return False, "SMTP server not found"
                
            except Exception as e:
                if attempt < retry_count - 1:
                    continue
                return False, "Email sending failed"
        
        return False, "Failed to send verification code"
    
    def store_otp(self, session, otp, email):
        """Store OTP in session with expiration"""
        session['otp'] = otp
        session['otp_email'] = email
        session['otp_expires'] = (datetime.now() + timedelta(minutes=5)).isoformat()
        session['otp_attempts'] = 0
        session['last_otp_sent'] = datetime.now().isoformat()
    
    def verify_otp(self, session, entered_otp):
        """Verify OTP from session"""
        stored_otp = session.get('otp')
        otp_expires = session.get('otp_expires')
        
        if not stored_otp or not otp_expires:
            return False, "No OTP found"
        
        # Check expiration
        if datetime.now() > datetime.fromisoformat(otp_expires):
            return False, "OTP expired"
        
        # Check attempts
        attempts = session.get('otp_attempts', 0)
        if attempts >= 3:
            return False, "Too many attempts"
        
        # Verify OTP
        if stored_otp == entered_otp:
            return True, "OTP verified"
        else:
            session['otp_attempts'] = attempts + 1
            return False, f"Invalid OTP. {3 - (attempts + 1)} attempts remaining"
    
    def can_resend_otp(self, session):
        """Check if OTP can be resent (30s cooldown)"""
        last_sent = session.get('last_otp_sent')
        if not last_sent:
            return True
        
        last_sent_time = datetime.fromisoformat(last_sent)
        return datetime.now() > last_sent_time + timedelta(seconds=30)
    
    def clear_otp(self, session):
        """Clear OTP data from session"""
        keys_to_remove = ['otp', 'otp_email', 'otp_expires', 'otp_attempts', 'last_otp_sent', 'pending_login']
        for key in keys_to_remove:
            session.pop(key, None)