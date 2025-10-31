import os
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse 

# --- IMPORTANT SECURITY NOTE ---
# For a production application, you should NEVER hardcode sensitive information
# like email passwords directly in your code. Use environment variables.
# This example keeps your hardcoded values as per your request, but be aware
# this is not secure for public repositories or production environments.
# -------------------------------

app = FastAPI()

# --- CORS Configuration ---
# Allows your Netlify frontend to communicate with this backend.
origins = [
    "https://tenzindevelopment.netlify.app", # Your Netlify frontend URL
    # Add other origins if needed for local testing:
    # "http://localhost",
    # "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          
    allow_credentials=True,         
    allow_methods=["*"],            
    allow_headers=["*"],            
)
# --------------------------

# --- SMTP Configuration ---
# Switched to Port 465 (SMTPS) for better compatibility with some hosts (like Render)
YOUR_EMAIL_ACCOUNT = "dtenzin.nov@gmail.com"  # Your actual sender email
YOUR_EMAIL_PASSWORD = "yhrv iivf sajq zpdl" # Your Gmail App Password
SMTP_SERVER = "smtp.gmail.com"           
SMTP_PORT = 465                          # SMTPS (SSL) port

RECIPIENT_EMAIL = "dtenzin.nov@gmail.com" # The email address where messages will be sent
# --------------------------

@app.post("/send-message/")
async def send_message(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    """
    Receives contact form data and attempts to send it as an email via SMTPS (Port 465).
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
        msg["From"] = YOUR_EMAIL_ACCOUNT 
        msg["To"] = RECIPIENT_EMAIL
        msg["Reply-To"] = email 

        # Connect to the SMTP server using SMTPS (Port 465)
        # We use smtplib.SMTP_SSL instead of smtplib.SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            # server.starttls() is NOT needed for SMTP_SSL on port 465
            server.login(YOUR_EMAIL_ACCOUNT, YOUR_EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Email sent successfully from {name} ({email}) to {RECIPIENT_EMAIL}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": "Your message has been sent successfully!"}
        )

    except smtplib.SMTPAuthenticationError:
        # This will happen if the App Password or email is incorrect
        print("SMTP Authentication Error: Check YOUR email username and App Password.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail={"status": "error", "message": "Failed to send message: Authentication failed."}
        )
    except smtplib.SMTPConnectError:
        # This will happen if the network connection fails
        print(f"SMTP Connection Error: Could not connect to {SMTP_SERVER}:{SMTP_PORT}. Check server firewall/connectivity.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail={"status": "error", "message": "Failed to send message: Could not connect to email server. (Check firewall)"}
        )
    except Exception as e:
        # Catch all other exceptions, including the "Network is unreachable" error
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": f"An unexpected error occurred. Error detail: {e}"}
        )
