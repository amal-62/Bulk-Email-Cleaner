import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
from app.models.user import User

def get_gmail_service(user: User):
    """
    Creates an authenticated Gmail API client for a specific user
    using their stored access token.
    """
    credentials = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    )
    return build("gmail", "v1", credentials=credentials)


def fetch_emails(user: User, max_results: int = 20):
    """
    Fetches the latest emails from the user's Gmail inbox.
    Returns a list of email summaries.
    """
    service = get_gmail_service(user)

    # Get list of message IDs from inbox
    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"]
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        # Fetch full message details for each ID
        message = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        # Extract headers into a dict for easy access
        headers = {
            h["name"]: h["value"]
            for h in message["payload"]["headers"]
        }

        emails.append({
            "id": message["id"],
            "thread_id": message["threadId"],
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "snippet": message.get("snippet", ""),
        })

    return emails


def fetch_email_body(user: User, message_id: str):
    """
    Fetches the full body of a specific email.
    Gmail stores email content as base64-encoded parts.
    """
    service = get_gmail_service(user)

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    # Extract the email body from the message parts
    body = ""
    payload = message.get("payload", {})
    parts = payload.get("parts", [])

    if parts:
        for part in parts:
            # Look for plain text version of the email
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                # Gmail encodes body as URL-safe base64
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                break
    else:
        # Some emails have body directly in payload
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8")

    return {
        "id": message["id"],
        "subject": next(
            (h["value"] for h in payload["headers"] if h["name"] == "Subject"),
            "(no subject)"
        ),
        "body": body,
        "snippet": message.get("snippet", ""),
    }