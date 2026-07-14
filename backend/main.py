import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse 

# Load local .env file for development.
# In production, set SENDGRID_API_KEY in the host environment.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# --- IMPORTANT SECURITY NOTE ---
# Use environment variables for API keys and sensitive credentials.
# Set SENDGRID_API_KEY in your Render (or hosting) environment variables.
# -------------------------------

app = FastAPI()

# --- CORS Configuration ---
# Allows your Netlify frontend to communicate with this backend.
origins = [
    "https://tenzindevelopment.netlify.app", # Your Netlify frontend URL
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
]

# Netlify deploy previews and branch deploys get their own subdomains,
# e.g. deploy-preview-3--tenzindevelopment.netlify.app
ORIGIN_REGEX = r"https://[a-z0-9-]+--tenzindevelopment\.netlify\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/")
async def health():
    """Cheap endpoint the frontend pings to wake the service before a user submits."""
    return {"status": "ok"}
# --------------------------

# --- SendGrid Configuration ---
YOUR_EMAIL_ACCOUNT = "dtenzin.nov@gmail.com"  # Your sender email address
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

RECIPIENT_EMAIL = "dtenzin.nov@gmail.com" # The email address where messages will be sent

# Every contact email carries this tag in its subject. The Gmail filter
# ("Matches: subject:(PortfolioContact-9f2a) -> Never send it to Spam")
# keys off it, so changing this string will send mail back to the spam folder.
SUBJECT_TAG = "[PortfolioContact-9f2a]"
# --------------------------

@app.get("/debug-sendgrid/")
async def debug_sendgrid():
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    return {
        "sendgrid_api_key_present": bool(sendgrid_api_key),
        "sendgrid_api_key_sample": None if not sendgrid_api_key else f"{sendgrid_api_key[:4]}...{sendgrid_api_key[-4:]}",
    }

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
        if not SENDGRID_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"status": "error", "message": "SendGrid API key is not configured."}
            )

        # Mail sent through SendGrid but claiming to be from a gmail.com address cannot
        # pass SPF/DKIM alignment, so Gmail files it as spam. SUBJECT_TAG is the stable
        # anchor for the Gmail filter that overrides this — do not change it casually.
        payload = {
            "personalizations": [
                {
                    "to": [{"email": RECIPIENT_EMAIL}],
                    "subject": f"{SUBJECT_TAG} {name} <{email}>"
                }
            ],
            "from": {"email": YOUR_EMAIL_ACCOUNT, "name": "Portfolio Contact"},
            "reply_to": {"email": email, "name": name},
            "content": [
                {
                    "type": "text/plain",
                    "value": f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(SENDGRID_API_URL, json=payload, headers=headers, timeout=20)

        if response.status_code not in (200, 201, 202):
            print(f"SendGrid error: {response.status_code} {response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "status": "error",
                    "message": "Failed to send message via SendGrid.",
                    "sendgrid_status": response.status_code,
                    "sendgrid_response": response.text,
                }
            )

        print(f"Email sent successfully via SendGrid from {name} ({email}) to {RECIPIENT_EMAIL}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": "Your message has been sent successfully!"}
        )

    except requests.exceptions.RequestException as e:
        print(f"SendGrid request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"status": "error", "message": "Failed to send message: email provider request error."}
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": f"An unexpected error occurred. Error detail: {e}"}
        )
