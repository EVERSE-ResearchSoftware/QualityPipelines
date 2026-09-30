"""Lookup of the canonical EVERSE indicator vocabulary."""

import requests

VOCABULARY_URL = "https://everse.software/indicators/api/indicators.json"
MISSING_ID = "missing"

_vocabulary_cache = None


def _fetch_vocabulary():
    """
    Fetches the EVERSE indicator vocabulary API response's `indicators` list.
    The result is cached for the lifetime of the process.
    """
    global _vocabulary_cache
    if _vocabulary_cache is None:
        response = requests.get(VOCABULARY_URL, timeout=10)
        response.raise_for_status()
        _vocabulary_cache = response.json()["indicators"]
    return _vocabulary_cache


def fetch_known_indicator_ids():
    """
    Fetches the set of canonical indicator @id URIs from the EVERSE
    indicator vocabulary API.
    """
    return frozenset(indicator["@id"] for indicator in _fetch_vocabulary())


def fetch_indicator_id_by_abbreviation():
    """
    Fetches a mapping of canonical indicator abbreviation (e.g.
    `software_has_license`) to its @id URI from the EVERSE indicator
    vocabulary API.
    """
    return {
        indicator["abbreviation"]: indicator["@id"]
        for indicator in _fetch_vocabulary()
    }


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
