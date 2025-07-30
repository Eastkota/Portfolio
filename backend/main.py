import os
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


# --- IMPORTANT SECURITY NOTE ---
# For a production application, you should NEVER hardcode sensitive information
# like email passwords directly in your code. Use environment variables.
# Example using python-dotenv:
# from dotenv import load_dotenv
# load_dotenv() # This loads variables from a .env file
# SENDER_EMAIL = os.getenv("SENDER_EMAIL")
# SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
# SMTP_SERVER = os.getenv("SMTP_SERVER")
# SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
# -------------------------------

app = FastAPI()

# Determine the base directory of the project
project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(project_root_dir, "frontend")

# Ensure the 'frontend' directory exists
if not os.path.exists(frontend_dir):
    print(f"Error: Frontend directory '{frontend_dir}' not found.")
    print("Please ensure your project structure has a 'frontend' folder at the same level as the 'backend' folder.")
    exit(1)

# Initialize Jinja2Templates to render HTML
templates = Jinja2Templates(directory=frontend_dir)

# --- CORRECTED: Mount static files to a /static/ path ---
# This means assets like 'images/myself.jpg' will be accessed via '/static/images/myself.jpg'
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Define a root route to serve your index.html
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- SMTP Configuration ---
# These are YOUR email account credentials that the FastAPI app will use to LOG IN.
# The 'From' address in the email header will be the user's email from the form.
YOUR_EMAIL_ACCOUNT = "eastboy.tenzin@gmail.com"  # Your actual sender email
YOUR_EMAIL_PASSWORD = "iups cbdt acgj rjno" # Your actual email password or app-specific password
SMTP_SERVER = "smtp.gmail.com"           # Example: For Gmail. Use your email provider's SMTP server.
SMTP_PORT = 587                          # Common port for TLS/STARTTLS

RECIPIENT_EMAIL = "dtenzin.nov@gmail.com" # The email address where messages will be sent (your email)
# --------------------------

@app.post("/send-message/")
async def send_message(name: str = Form(...), email: str = Form(...), message: str = Form(...)):
    """
    Receives contact form data and attempts to send it as an email via SMTP.
    The email will appear to come from the user's provided email,
    but it's sent via YOUR configured email account.
    """
    try:
        # Create the email content
        # Set the 'From' header to the user's email from the form
        msg = MIMEText(f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}")
        msg["Subject"] = f"Portfolio Contact: Message from {name}"
        msg["From"] = email  # This makes the email appear to be from the user
        msg["To"] = RECIPIENT_EMAIL
        msg["Reply-To"] = email # So you can reply directly to the user

        # Connect to the SMTP server using YOUR_EMAIL_ACCOUNT credentials
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(YOUR_EMAIL_ACCOUNT, YOUR_EMAIL_PASSWORD) # Log in to YOUR email account
            server.send_message(msg) # Send the email

        print(f"Email sent successfully from {name} ({email}) to {RECIPIENT_EMAIL}")
        return {"status": "success", "message": "Your message has been sent successfully!"}

    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication Error: Check YOUR email username and password in main.py. If using Gmail with 2FA, use an App Password.")
        return {"status": "error", "message": "Failed to send message: Authentication failed. Please contact the site administrator."}
    except smtplib.SMTPConnectError:
        print(f"SMTP Connection Error: Could not connect to {SMTP_SERVER}:{SMTP_PORT}. Check server address and port.")
        return {"status": "error", "message": "Failed to send message: Could not connect to email server."}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": "An unexpected error occurred. Please try again later."}

