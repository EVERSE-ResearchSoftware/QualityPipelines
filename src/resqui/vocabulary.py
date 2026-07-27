"""Lookup of the canonical EVERSE indicator vocabulary."""

import requests

VOCABULARY_URL = "https://everse.software/indicators/api/indicators.json"
MISSING_ID = "missing"

_known_ids_cache = None


def fetch_known_indicator_ids():
    """
    Fetches the set of canonical indicator @id URIs from the EVERSE
    indicator vocabulary API. The result is cached for the lifetime of
    the process.
    """
    global _known_ids_cache
    if _known_ids_cache is None:
        response = requests.get(VOCABULARY_URL, timeout=10)
        response.raise_for_status()
        _known_ids_cache = frozenset(
            indicator["@id"] for indicator in response.json()["indicators"]
        )
    return _known_ids_cache


def is_known_indicator_id(indicator_id):
    """
    Whether `indicator_id` is either the "missing" sentinel or a W3ID URI
    listed in the EVERSE indicator vocabulary. If the vocabulary can't be
    fetched (e.g. no network access), validation is skipped and the id is
    treated as known so resqui remains usable offline.
    """
    if indicator_id == MISSING_ID:
        return True
    try:
        known_ids = fetch_known_indicator_ids()
    except requests.RequestException:
        return True
    return indicator_id in known_ids
