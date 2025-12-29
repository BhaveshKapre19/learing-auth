# Project Documentation

## Overview
This project is a Django-based Content Management System (CMS) with a robust authentication system. It includes features for user registration, multi-factor authentication (MFA), password management, and user profiles.

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <project_directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Apply migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Create a superuser:**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```

## API Documentation

### Authentication

#### Login
-   **Endpoint:** `/api/auth/login/`
-   **Method:** `POST`
-   **Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "yourpassword"
    }
    ```
-   **Response:** Returns access and refresh tokens, or an MFA requirement indication.

#### MFA Verification
-   **Endpoint:** `/api/auth/login/verify-mfa/`
-   **Method:** `POST`
-   **Body:**
    ```json
    {
        "email": "user@example.com",
        "code": "123456"
    }
    ```
-   **Response:** Returns access and refresh tokens.

#### Registration (Admin Only)
-   **Endpoint:** `/api/auth/register/`
-   **Method:** `POST`
-   **Permissions:** Admin User
-   **Body:**
    ```json
    {
        "email": "newuser@example.com",
        "first_name": "First",
        "last_name": "Last"
    }
    ```

#### Password Reset
-   **Request Reset:** `/api/auth/password/reset/`
-   **Confirm Reset:** `/api/auth/password/reset/confirm/`

#### User Profile
-   **Get Current User:** `/api/auth/me/`
-   **Method:** `GET`, `PATCH`

## Authentication Flow

1.  **Registration:** Admin registers a new user. The user receives a welcome email with a temporary password and a verification link.
2.  **Verification:** User clicks the email link to verify their account.
3.  **Login:** User logs in with email and temporary password.
4.  **Change Password:** Forced password change on first login.
5.  **MFA:** If enabled, user receives an email with a code to complete login.
