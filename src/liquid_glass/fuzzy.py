"""Forgiving text matching for search: typos, partial words and any word order."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

_WORD = re.compile(r"\w+")

# Words shorter than this must match exactly or as a prefix; longer words may contain typos.
MIN_FUZZY_LENGTH = 4
FUZZY_THRESHOLD = 0.75


def tokenize(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _token_score(query_word: str, word: str) -> float:
    if query_word == word:
        return 1.0
    if word.startswith(query_word):
        return 0.95
    if len(query_word) >= 3 and query_word in word:
        return 0.9
    if len(query_word) < MIN_FUZZY_LENGTH:
        return 0.0
    ratio = SequenceMatcher(None, query_word, word).ratio()
    return ratio if ratio >= FUZZY_THRESHOLD else 0.0


def score(query: str, text: str) -> float:
    """Return a 0..1 relevance score. Every word in the query must match something in text.

    A score of 0 means no match.
    """
    query_words = tokenize(query)
    text_words = tokenize(text)
    if not query_words:
        return 1.0
    if not text_words:
        return 0.0

    total = 0.0
    for query_word in query_words:
        best = max(_token_score(query_word, word) for word in text_words)
        if best == 0.0:
            return 0.0
        total += best
    return total / len(query_words)
