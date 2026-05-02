import os
from flask import session, url_for
from google_auth_oauthlib.flow import Flow
import msal
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "client_secrets.json")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]

MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_AUTHORITY = f"https://login.microsoftonline.com/{os.getenv('MS_TENANT_ID', 'common')}"
MS_SCOPES = ["Mail.ReadWrite"]

def get_google_flow(redirect_uri):
    return Flow.from_client_secrets_file(GOOGLE_CLIENT_SECRETS_FILE, scopes=GOOGLE_SCOPES, redirect_uri=redirect_uri)

def get_ms_msal_app():
    return msal.ConfidentialClientApplication(MS_CLIENT_ID, authority=MS_AUTHORITY, client_credential=MS_CLIENT_SECRET)

def get_ms_auth_url(redirect_uri):
    return get_ms_msal_app().get_authorization_request_url(MS_SCOPES, redirect_uri=redirect_uri)

def acquire_ms_token(code, redirect_uri):
    return get_ms_msal_app().acquire_token_by_authorization_code(code, MS_SCOPES, redirect_uri=redirect_uri)
