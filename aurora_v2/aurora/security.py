"""Secret hygiene: the platform must be unable to leak a key, not merely careful.

Every outbound surface is a leak risk - a log line, an error message, a commit, a
report. Careful review does not scale, so the rule is mechanical: nothing leaves
this process without passing through redact(), and a payload that still contains a
key-shaped string is refused rather than filtered, because a silent filter invites
trust in a redaction that already failed once.

This is deliberately conservative and slightly over-eager: a redacted price is an
inconvenience, a published key is a breach.
"""
import os
import re
from typing import Iterable, List

# Anything that looks like a credential: 32+ chars of key-shaped alphabet, or a
# known prefix. Kept narrow enough that ordinary prose and prices pass through.
_KEY_SHAPED = re.compile(r"\b[A-Za-z0-9_\-]{28,}\b")
_KNOWN_PREFIXES = ("sk-", "pk_", "ghp_", "gho_", "github_pat_", "xoxb-", "AIza", "hf_")
_ENV_NAMES = (
    "FRED_API_KEY", "TWELVEDATA_API_KEY", "FINNHUB_API_KEY", "FMP_API_KEY",
    "EODHD_API_KEY", "TIINGO_API_KEY", "ALPHAVANTAGE_API_KEY", "EIA_API_KEY",
    "GITHUB_ACCESS_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
)
MASK = "***REDACTED***"


def known_secrets(env=None) -> List[str]:
    """The actual secret values this process holds, longest first."""
    env = os.environ if env is None else env
    values = [env.get(name, "") for name in _ENV_NAMES]
    return sorted((v for v in values if v and len(v) >= 8), key=len, reverse=True)


def redact(text: str, secrets: Iterable[str] | None = None) -> str:
    """Mask every known secret value and every key-shaped token."""
    if text is None:
        return ""
    out = str(text)
    for secret in (known_secrets() if secrets is None else secrets):
        if secret:
            out = out.replace(secret, MASK)
    out = _KEY_SHAPED.sub(MASK, out)
    for prefix in _KNOWN_PREFIXES:
        out = re.sub(re.escape(prefix) + r"\S+", MASK, out)
    return out


def contains_secret(text: str, secrets: Iterable[str] | None = None) -> bool:
    if not text:
        return False
    if any(s and s in str(text) for s in (known_secrets() if secrets is None else secrets)):
        return True
    return bool(_KEY_SHAPED.search(str(text)))


def assert_safe(payload: str, what: str = "payload") -> str:
    """Use before anything is committed, logged or sent. Refuses, not sanitises."""
    if contains_secret(payload):
        raise PermissionError(
            f"{what} contains key-shaped material; refusing to publish it "
            f"(redact() first and inspect why a secret reached this point)")
    return payload
