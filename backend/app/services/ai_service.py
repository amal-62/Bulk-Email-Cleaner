import os
import json
from groq import Groq

# Initialise the Groq client using our API key from .env
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def summarise_and_categorise_email(subject: str, sender: str, body: str) -> dict:
    """
    Sends an email to an AI model via Groq and gets back:
    - A short summary (2-3 sentences)
    - A category (Urgent, Newsletter, Receipt, Social, Spam, Other)
    - A priority score (1-5, where 5 is most urgent)
    - Whether action is needed
    """

    prompt = f"""You are an email assistant. Analyse this email and respond with ONLY a JSON object, no other text.

Email details:
Subject: {subject}
From: {sender}
Body: {body[:2000]}

Respond with exactly this JSON structure:
{{
    "summary": "2-3 sentence summary of what this email is about",
    "category": "one of: Urgent, Newsletter, Receipt, Social, Spam, Other",
    "priority": <number from 1-5 where 5 is most urgent>,
    "action_needed": <true or false>
}}"""

    # Send the prompt to Groq's AI model
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Free, fast, and very capable model
        max_tokens=300,
        messages=[
            {
                "role": "system",
                "content": "You are an email assistant. Always respond with valid JSON only, no other text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Extract the text response
    response_text = response.choices[0].message.content

    # Parse JSON response into Python dictionary
    try:
        # Strip any accidental markdown code fences if present
        clean = response_text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        result = {
            "summary": "Could not generate summary",
            "category": "Other",
            "priority": 1,
            "action_needed": False
        }

    return result


def categorise_email_list(emails: list) -> list:
    """
    Takes a list of emails and categorises each one.
    Uses snippet instead of full body to save API calls.
    """
    categorised = []

    for email in emails:
        result = summarise_and_categorise_email(
            subject=email.get("subject", ""),
            sender=email.get("from", ""),
            body=email.get("snippet", "")
        )

        # Merge original email data with AI results
        categorised.append({
            **email,
            "summary": result.get("summary", ""),
            "category": result.get("category", "Other"),
            "priority": result.get("priority", 1),
            "action_needed": result.get("action_needed", False)
        })

    return categorised