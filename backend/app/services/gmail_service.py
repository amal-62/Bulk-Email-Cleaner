import os
import asyncio
from datetime import datetime
from email.utils import parseaddr, parsedate_to_datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.user import User
from app.models.email import Email


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

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"]
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        message = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

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
    """
    service = get_gmail_service(user)

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    body = ""
    payload = message.get("payload", {})
    parts = payload.get("parts", [])

    if parts:
        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                break
    else:
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


# ---------------------------------------------------------------------------
# Sync: paginate through Gmail, fetch metadata concurrently, upsert into DB
# ---------------------------------------------------------------------------

def _parse_gmail_date(date_str: str):
    """Gmail's Date header isn't always uniform — fall back to None if it can't be parsed."""
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def _fetch_message_metadata(user: User, message_id: str):
    """
    Blocking call — must be run via asyncio.to_thread.
    Builds its own Gmail service instance rather than reusing a shared one:
    the underlying httplib2 client is NOT thread-safe, so sharing a single
    service across concurrent threads corrupts memory and can crash the process.
    """
    service = get_gmail_service(user)
    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["From", "Subject", "Date", "List-Unsubscribe"]
    ).execute()

    headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
    sender_name, sender_email = parseaddr(headers.get("From", ""))

    unsubscribe_header = headers.get("List-Unsubscribe")

    return {
        "gmail_message_id": message["id"],
        "sender_email": sender_email or "unknown",
        "sender_name": sender_name or None,
        "subject": headers.get("Subject"),
        "received_at": _parse_gmail_date(headers.get("Date", "")),
        "has_unsubscribe_header": bool(unsubscribe_header),
        "unsubscribe_url": unsubscribe_header,
    }


async def _fetch_message_metadata_async(user: User, message_id: str):
    return await asyncio.to_thread(_fetch_message_metadata, user, message_id)


def _list_all_message_ids(service, max_emails: int):
    """Paginates through Gmail until max_emails is reached or messages run out."""
    message_ids = []
    page_token = None

    while len(message_ids) < max_emails:
        remaining = max_emails - len(message_ids)
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=min(500, remaining),
            pageToken=page_token
        ).execute()

        batch = results.get("messages", [])
        message_ids.extend(m["id"] for m in batch)

        page_token = results.get("nextPageToken")
        if not page_token or not batch:
            break

    return message_ids[:max_emails]


async def sync_emails(user, db, max_emails: int = 2000, concurrency: int = 20):
    """
    Full sync: paginate Gmail, fetch metadata concurrently, upsert into the DB.
    Returns the number of emails synced.
    """
    # Pagination itself is fine on a single thread/service — it's the
    # concurrent per-message fetches below that need their own service each.
    listing_service = get_gmail_service(user)
    message_ids = await asyncio.to_thread(_list_all_message_ids, listing_service, max_emails)

    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_fetch(mid):
        async with semaphore:
            return await _fetch_message_metadata_async(user, mid)

    results = await asyncio.gather(
        *(bounded_fetch(mid) for mid in message_ids),
        return_exceptions=True
    )

    synced_count = 0
    for r in results:
        if isinstance(r, Exception):
            continue

        stmt = pg_insert(Email).values(
            user_id=user.id,
            **r,
            synced_at=datetime.utcnow()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["gmail_message_id"],
            set_={
                "subject": stmt.excluded.subject,
                "received_at": stmt.excluded.received_at,
                "has_unsubscribe_header": stmt.excluded.has_unsubscribe_header,
                "unsubscribe_url": stmt.excluded.unsubscribe_url,
                "synced_at": stmt.excluded.synced_at,
            }
        )
        db.execute(stmt)
        synced_count += 1

    db.commit()
    return synced_count


# ---------------------------------------------------------------------------
# Trash: move real Gmail messages to trash, concurrently
# ---------------------------------------------------------------------------

def _trash_message(user: User, message_id: str):
    """
    Blocking call — must be run via asyncio.to_thread.
    Builds its own service per call for the same thread-safety reason as sync.
    """
    service = get_gmail_service(user)
    service.users().messages().trash(userId="me", id=message_id).execute()
    return message_id


async def _trash_message_async(user: User, message_id: str):
    return await asyncio.to_thread(_trash_message, user, message_id)


async def trash_messages(user, db, sender_emails: list[str], concurrency: int = 20):
    """
    For the given sender emails, finds all of that user's synced Email rows,
    trashes each one in real Gmail, and marks it is_trashed=True in the DB
    (only for the ones that actually succeeded in Gmail).
    Returns (trashed_count, failed_count).
    """
    rows = (
        db.query(Email)
        .filter(
            Email.user_id == user.id,
            Email.sender_email.in_(sender_emails),
            Email.is_trashed == False,
        )
        .all()
    )

    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_trash(row):
        async with semaphore:
            try:
                await _trash_message_async(user, row.gmail_message_id)
                return row, None
            except Exception as e:
                return row, e

    results = await asyncio.gather(*(bounded_trash(row) for row in rows))

    trashed_count = 0
    failed_count = 0
    for row, error in results:
        if error is None:
            row.is_trashed = True
            trashed_count += 1
        else:
            failed_count += 1

    db.commit()
    return trashed_count, failed_count


# ---------------------------------------------------------------------------
# Unsubscribe: follow the real List-Unsubscribe mechanism per sender
# ---------------------------------------------------------------------------

import re
import requests
from email.mime.text import MIMEText
from urllib.parse import unquote


def _send_unsubscribe_email(user: User, mailto_url: str):
    """
    Handles a mailto: List-Unsubscribe value by sending a real (blank)
    email to the address it specifies, exactly as an email client would.
    """
    # mailto: links can carry query params, e.g. mailto:x@y.com?subject=unsubscribe
    address_part = mailto_url[len("mailto:"):]
    to_address, _, query = address_part.partition("?")
    to_address = unquote(to_address)
    subject = "unsubscribe"
    if query:
        match = re.search(r"subject=([^&]+)", query, re.IGNORECASE)
        if match:
            subject = unquote(match.group(1).replace("+", " "))

    service = get_gmail_service(user)
    message = MIMEText("")
    message["to"] = to_address
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _visit_unsubscribe_link(http_url: str):
    """
    Handles an http(s) List-Unsubscribe value by requesting the link.
    Many providers implement RFC 8058 one-click unsubscribe, which expects
    a POST — we try POST first and fall back to GET for providers that
    just expect a visit.
    """
    try:
        resp = requests.post(http_url, timeout=10)
        if resp.status_code < 400:
            return
    except requests.RequestException:
        pass
    requests.get(http_url, timeout=10).raise_for_status()


def _parse_unsubscribe_targets(header_value: str) -> list[str]:
    """
    The List-Unsubscribe header looks like:
        <mailto:unsub@example.com>, <https://example.com/unsub?id=123>
    We store the raw header, so pull the targets out here.
    http(s) links come first, mailto: second.
    """
    targets = re.findall(r"<\s*([^<>\s]+)\s*>", header_value or "")
    if not targets:
        targets = [t.strip() for t in (header_value or "").split(",") if t.strip()]
    https = [t for t in targets if t.lower().startswith("http")]
    mailto = [t for t in targets if t.lower().startswith("mailto:")]
    return https + mailto


def _unsubscribe_one(user: User, unsubscribe_header: str):
    """Blocking — must be run via asyncio.to_thread."""
    targets = _parse_unsubscribe_targets(unsubscribe_header)
    if not targets:
        raise ValueError(f"Unrecognized unsubscribe mechanism: {unsubscribe_header}")

    last_error = None
    for target in targets:
        try:
            if target.lower().startswith("mailto:"):
                _send_unsubscribe_email(user, target)
            else:
                _visit_unsubscribe_link(target)
            return
        except Exception as e:
            last_error = e
    raise last_error


async def _unsubscribe_one_async(user: User, unsubscribe_url: str):
    return await asyncio.to_thread(_unsubscribe_one, user, unsubscribe_url)


async def unsubscribe_senders(user, db, sender_emails: list[str], concurrency: int = 10):
    """
    For each given sender, finds one representative unsubscribe_url from
    their synced emails and attempts to unsubscribe via the real mechanism
    (mailto or http). Returns (succeeded_count, failed_count).
    Note: a successful HTTP response doesn't guarantee the sender's system
    actually processes the unsubscribe — that part is out of our control.
    """
    # One representative URL per sender is enough — unsubscribing once
    # per sender covers all their emails, we don't need to hit it per-message.
    rows = (
        db.query(Email.sender_email, func.max(Email.unsubscribe_url).label("unsubscribe_url"))
        .filter(
            Email.user_id == user.id,
            Email.sender_email.in_(sender_emails),
            Email.has_unsubscribe_header == True,
        )
        .group_by(Email.sender_email)
        .all()
    )

    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_unsub(row):
        async with semaphore:
            try:
                await _unsubscribe_one_async(user, row.unsubscribe_url)
                return None
            except Exception as e:
                return e

    results = await asyncio.gather(*(bounded_unsub(row) for row in rows))

    succeeded = sum(1 for r in results if r is None)
    failed = sum(1 for r in results if r is not None)
    return succeeded, failed