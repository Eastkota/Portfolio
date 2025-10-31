import os
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, Request, Form, HTTPException, status
# IMPORTANT: Import CORSMiddleware for cross-origin requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse # Use JSONResponse for API responses

# --- IMPORTANT SECURITY NOTE ---
# For a production application, you should NEVER hardcode sensitive information
# like email passwords directly in your code. Use environment variables.
# This example keeps your hardcoded values as per your request, but be aware
# this is not secure for public repositories or production environments.
# -------------------------------

app = FastAPI()

# --- CORS Configuration ---
# This middleware allows your Netlify frontend to communicate with this backend.
# Replace 'https://tenzindevelopment.netlify.app' with your actual Netlify domain.
# If you have a custom domain for your frontend, add it here too.
origins = [
    "https://tenzindevelopment.netlify.app", # Your Netlify frontend URL
    # Add other origins if needed, e.g., for local development:
    # "http://localhost",
    # "http://localhost:8000",
    # "http://127.0.0.1:5500", # Example for VS Code Live Server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Specifies which origins are allowed
    allow_credentials=True,         # Allows cookies to be included in cross-origin requests
    allow_methods=["*"],            # Allows all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],            # Allows all headers
)
# --------------------------

# --- SMTP Configuration ---
# These are YOUR email account credentials that the FastAPI app will use to LOG IN.
# The 'From' address in the email header will be your sender email.
YOUR_EMAIL_ACCOUNT = "dtenzin.nov@gmail.com"  # Your actual sender email
YOUR_EMAIL_PASSWORD = "Galing@2000" # Your actual email password or app-specific password
SMTP_SERVER = "smtp.gmail.com"           # Example: For Gmail. Use your email provider's SMTP server.
SMTP_PORT = 587                          # Common port for TLS/STARTTLS

RECIPIENT_EMAIL = "dtenzin.nov@gmail.com" # The email address where messages will be sent (your email)
# --------------------------

@app.post("/send-message/")
async def send_message(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    """
    Receives contact form data and attempts to send it as an email via SMTP.
    The email will appear to come from YOUR configured email account,
    but the 'Reply-To' will be set to the user's provided email.
    """
    # Basic validation
    if not all([name, email, message]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "All fields are required."}
        )

    try:
        # Create the email content
        msg = MIMEText(f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}")
        msg["Subject"] = f"Portfolio Contact: Message from {name}"
        msg["From"] = YOUR_EMAIL_ACCOUNT # The email will be sent from your account
        msg["To"] = RECIPIENT_EMAIL
        msg["Reply-To"] = email # So you can reply directly to the user

        # Connect to the SMTP server using YOUR_EMAIL_ACCOUNT credentials
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(YOUR_EMAIL_ACCOUNT, YOUR_EMAIL_PASSWORD) # Log in to YOUR email account
            server.send_message(msg) # Send the email

        print(f"Email sent successfully from {name} ({email}) to {RECIPIENT_EMAIL}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": "Your message has been sent successfully!"}
        )

    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication Error: Check YOUR email username and password. If using Gmail with 2FA, use an App Password.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # More specific status code
            detail={"status": "error", "message": "Failed to send message: Authentication failed. Please contact the site administrator."}
        )
    except smtplib.SMTPConnectError:
        print(f"SMTP Connection Error: Could not connect to {SMTP_SERVER}:{SMTP_PORT}. Check server address and port.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, # More specific status code
            detail={"status": "error", "message": "Failed to send message: Could not connect to email server."}
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": "An unexpected error occurred. Please try again later."}
        )

