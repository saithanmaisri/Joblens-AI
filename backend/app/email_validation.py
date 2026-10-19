
"""Validate email addresses using EmailVerify.io."""
import os

import httpx

EMAILVERIFY_API_URL = "https://app.emailverify.io/api/v1/validate"


def validate_email_address(email: str) -> dict:
    api_key = os.getenv("EMAILVERIFY_API_KEY")

    if not api_key:
        raise RuntimeError("Email validation API is not configured.")

    try:
        response = httpx.get(
            EMAILVERIFY_API_URL,
            params={
                "key": api_key,
                "email": email.strip().lower(),
            },
            timeout=15.0,
        )
        response.raise_for_status()
        result = response.json()

    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("Email validation service is unavailable.") from exc

    if not isinstance(result, dict):
        raise RuntimeError("Unexpected email validation response.")

    return result
