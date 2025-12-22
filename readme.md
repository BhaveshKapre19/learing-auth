1. Email Verification Template
Location: 
verification_email.html

Purpose: Send users a verification link to activate their account after registration.

Design Features:

Purple gradient header (#667eea to #764ba2)
Prominent "Verify Email Address" call-to-action button
Expiration time notice
Security warnings
Alternative link for manual copy-paste
Fully responsive design
Context Variables:

{
    'user': User object,
    'verification_url': 'https://example.com/verify/abc123...',
    'expiration_hours': 24,
    'site_name': 'Your Site Name',
    'current_year': 2025
}




2. Password Reset Template
Location: 
reset_password_email.html

Purpose: Allow users to securely reset their password via a signed URL.

Design Features:

Pink-red gradient header (#f093fb to #f5576c)
"Reset Your Password" action button
Request details (time, IP address) for security
Comprehensive security tips
Warning notices for unauthorized attempts
Context Variables:

{
    'user': User object,
    'reset_url': 'https://example.com/reset-password/xyz789...',
    'expiration_hours': 1,
    'request_time': '2025-12-22 12:00:00 UTC',
    'request_ip': '192.168.1.100',
    'site_name': 'Your Site Name',
    'current_year': 2025
}




3. MFA Code Template
Location: 
mfa_code_email.html

Purpose: Deliver two-factor authentication codes for enhanced login security.

Design Features:

Blue gradient header (#4facfe to #00f2fe)
Large, prominent code display with monospace font
5-minute expiration notice
Login attempt details (time, IP, device)
Security best practices section
Clear visual hierarchy
Context Variables:

{
    'user': User object,
    'mfa_code': 'A7K9P2',
    'validity_minutes': 5,
    'request_time': '2025-12-22 12:00:00 UTC',
    'request_ip': '192.168.1.100',
    'device_info': 'Chrome on Windows',
    'site_name': 'Your Site Name',
    'current_year': 2025
}



4. Onboarding/Welcome Template
Location: 
welcome_email.html

Purpose: Welcome new users and provide temporary credentials for first login.

Design Features:

Green-cyan gradient header (#43e97b to #38f9d7)
Welcoming emoji and messaging
Credentials display box (email + temporary password)
Step-by-step getting started guide
Account features overview
"Activate Account & Login" button
Context Variables:

{
    'user': User object,
    'temp_password': 'TempPass123!',
    'expiration_hours': 24,
    'activation_url': 'https://example.com/activate/token123...',
    'support_url': 'https://example.com/support',
    'site_name': 'Your Site Name',
    'current_year': 2025
}