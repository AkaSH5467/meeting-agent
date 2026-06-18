import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

PERSONAL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "icloud.com", "me.com", "mac.com", "googlemail.com",
    "protonmail.com", "proton.me", "live.com", "msn.com",
}


GENERIC_VENDOR_DOMAINS = {
    "google.com", "microsoft.com", "amazon.com", "apple.com",
    "meta.com", "facebook.com", "twitter.com", "x.com",
    "zoom.us", "webex.com", "slack.com", "salesforce.com",
}

# Generic words that look capitalised but are NOT company names.
GENERIC_WORDS = {
    "marketing", "sales", "tech", "technology", "engineering", "product",
    "design", "finance", "legal", "hr", "ops", "operations", "strategy",
    "meeting", "call", "sync", "demo", "review", "catchup", "catch",
    "weekly", "monthly", "quarterly", "annual", "internal", "external",
    "follow", "intro", "kickoff", "standup", "planning", "update",
    "check", "debrief", "wrap", "onboarding", "discovery", "up", "genai",
    "ai", "ml", "data", "cloud", "digital", "innovation", "dev", "it",
}

# Common first names — titles like "Catch up - Ravi" are personal, not company.
COMMON_FIRST_NAMES = {
    "ravi", "priya", "amit", "ankit", "neha", "rahul", "john", "jane",
    "mike", "sara", "alex", "chris", "david", "james", "robert", "lisa",
    "mark", "paul", "anna", "peter", "raj", "sam", "tom", "emma",
    "vijay", "arun", "deepa", "pooja", "sanjay", "arjun", "divya",
    "suresh", "ramesh", "mahesh", "ganesh", "lakshmi", "kavya", "srishti",
}


KNOWN_BRANDS: dict[str, str] = {
    "AT&T": "att.com",
    "T-Mobile": "t-mobile.com",
    "S&P": "spglobal.com",
    "H&M": "hm.com",
    "M&T Bank": "mtb.com",
    "Ernst & Young": "ey.com",
    "E&Y": "ey.com",
    "PwC": "pwc.com",
    "KPMG": "kpmg.com",
    "IBM": "ibm.com",
    "SAP": "sap.com",
    "HP": "hp.com",
    "GE": "ge.com",
    "3M": "3m.com",
    "McKinsey": "mckinsey.com",
    "Deloitte": "deloitte.com",
    "Accenture": "accenture.com",
    "Capgemini": "capgemini.com",
    "Infosys": "infosys.com",
    "Wipro": "wipro.com",
    "TCS": "tcs.com",
    "HCL": "hcltech.com",
    "BCG": "bcg.com",
    "Bain": "bain.com",
}


def extract_domain_from_email(email: str) -> Optional[str]:
    match = re.search(r"@([^@]+)$", email)
    if match:
        domain = match.group(1).lower()
        if domain not in PERSONAL_DOMAINS:
            return domain
    return None


def _is_generic(name: str) -> bool:
    """Return True if every word in the name is a generic/meeting word or a first name."""
    words = re.findall(r"[a-zA-Z]+", name.lower())
    if not words:
        return True
    return all(w in GENERIC_WORDS or w in COMMON_FIRST_NAMES for w in words)


def extract_company_from_title(title: str) -> Optional[Tuple[str, str]]:
    """
    Extract company from meeting title. Priority:
      1. KNOWN_BRANDS whole-word lookup (handles AT&T, IBM, GE etc. precisely)
      2. Explicit "with <Company>" / "@ <Company>" pattern
      3. Capitalised noun(s) before a meeting keyword — only if not generic/name
    """
    if not title:
        return None

    for brand, domain in KNOWN_BRANDS.items():
        # Escape special regex chars in brand name, then require word boundaries
        escaped = re.escape(brand)
        if re.search(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", title, re.IGNORECASE):
            logger.debug(f"[PARSER] Known brand match: {brand}")
            return brand, domain

    # ── 2. Explicit "with / @ / - <Company>" pattern ─────────────────────────
    explicit = re.search(
        r"(?:with|@)\s+([A-Z][A-Za-z0-9&.,'\- ]{1,40}?)"
        r"(?=\s+(?:call|meeting|sync|demo|review|chat|catchup|catch.up)|\s*$)",
        title, re.IGNORECASE
    )
    if explicit:
        name = explicit.group(1).strip().rstrip(",-")
        if name and not _is_generic(name):
            domain_guess = re.sub(r"[^a-z0-9]", "", name.lower()) + ".com"
            logger.debug(f"[PARSER] Explicit pattern match: {name}")
            return name, domain_guess

    # ── 3. Capitalised word(s) directly before a meeting keyword ─────────────
    generic = re.search(
        r"\b([A-Z][a-zA-Z0-9]{2,}(?:\s[A-Z][a-zA-Z0-9]{2,})?)"
        r"\s+(?:call|meeting|sync|demo|review|chat|catchup|catch.up)\b",
        title, re.IGNORECASE
    )
    if generic:
        name = generic.group(1).strip()
        if not _is_generic(name):
            domain_guess = re.sub(r"[^a-z0-9]", "", name.lower()) + ".com"
            logger.debug(f"[PARSER] Generic pattern match: {name}")
            return name, domain_guess

    return None


def extract_domain_from_description(description: str) -> Optional[str]:
    if not description:
        return None
    domain_pattern = r"\b([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:com|io|co|net|org|ai|dev))\b"
    matches = re.findall(domain_pattern, description.lower())
    for match in matches:
        if match not in PERSONAL_DOMAINS and not match.startswith("www."):
            return match
    return None


def domain_to_company_name(domain: str) -> str:
    root = domain.split(".")[0]
    return "".join(word.capitalize() for word in re.split(r"[-_]", root))


def _emails_from_event(event: dict) -> list[str]:
    emails = []
    for a in event.get("attendees", []):
        if isinstance(a, dict):
            emails.append(a.get("email", ""))
        else:
            emails.append(str(a))
    return emails


def extract_company(event: dict) -> Optional[Tuple[str, str]]:
    """
    Priority:
      1. Company name found in meeting title   ← always wins if present
      2. Non-personal, non-generic-vendor attendee email domain
      3. Generic vendor domain (google.com etc.) as last-resort email signal
      4. Domain found in event description
    """
    title = event.get("summary", "") or event.get("title", "")

    # ── 1. Title takes absolute priority ────────────────────────────────────
    title_result = extract_company_from_title(title)
    if title_result:
        logger.debug(f"[PARSER] Company from title: {title_result}")
        return title_result

    # ── 2. Attendee emails — skip personal AND generic vendor domains ────────
    emails = _emails_from_event(event)
    generic_vendor_hits = []

    for email in emails:
        domain = extract_domain_from_email(email)
        if not domain:
            continue
        if domain in GENERIC_VENDOR_DOMAINS:
            generic_vendor_hits.append((domain_to_company_name(domain), domain))
            continue
        logger.debug(f"[PARSER] Company from attendee email: {domain}")
        return domain_to_company_name(domain), domain

    # ── 3. Fall back to generic vendor if that's all we have ────────────────
    if generic_vendor_hits:
        logger.debug(f"[PARSER] Fallback to vendor email: {generic_vendor_hits[0]}")
        return generic_vendor_hits[0]

    # ── 4. Description ───────────────────────────────────────────────────────
    description = event.get("description", "")
    domain = extract_domain_from_description(description)
    if domain:
        logger.debug(f"[PARSER] Company from description: {domain}")
        return domain_to_company_name(domain), domain

    logger.debug(f"[PARSER] No company found for: {title}")
    return None