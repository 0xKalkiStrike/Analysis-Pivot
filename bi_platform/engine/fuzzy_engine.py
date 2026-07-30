"""Fuzzy string matching using RapidFuzz + custom phonetic helpers."""
from __future__ import annotations

import re
from typing import Iterable

from rapidfuzz import fuzz, process

from ..core.logger import get_logger

log = get_logger(__name__)

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


class FuzzyEngine:
    """Unified interface over multiple similarity algorithms."""

    ALGOS = {
        "ratio": fuzz.ratio,
        "partial": fuzz.partial_ratio,
        "token_sort": fuzz.token_sort_ratio,
        "token_set": fuzz.token_set_ratio,
        "weighted_ratio": fuzz.WRatio,
        "quick_ratio": fuzz.QRatio,
    }

    def __init__(self, algorithm: str = "weighted_ratio") -> None:
        if algorithm not in self.ALGOS:
            raise ValueError(f"Unknown algorithm '{algorithm}'. Choose from {list(self.ALGOS)}")
        self.algorithm = algorithm
        self.scorer = self.ALGOS[algorithm]

    def score(self, a: str, b: str) -> float:
        if a is None or b is None:
            return 0.0
        return float(self.scorer(str(a), str(b)))

    def best_match(self, needle: str, haystack: Iterable[str], threshold: float = 80.0) -> tuple[str, float] | None:
        result = process.extractOne(needle, list(haystack), scorer=self.scorer, score_cutoff=threshold)
        if result is None:
            return None
        return result[0], float(result[1])

    def top_matches(self, needle: str, haystack: Iterable[str], limit: int = 5, threshold: float = 60.0) -> list[tuple[str, float]]:
        results = process.extract(needle, list(haystack), scorer=self.scorer, limit=limit, score_cutoff=threshold)
        return [(r[0], float(r[1])) for r in results]

    # --------------------------------------------------------------- phonetic
    @staticmethod
    def soundex(word: str) -> str:
        if not word:
            return "0000"
        word = word.upper()
        first, tail = word[0], word[1:]
        mapping = {**dict.fromkeys("BFPV", "1"), **dict.fromkeys("CGJKQSXZ", "2"),
                   **dict.fromkeys("DT", "3"), "L": "4",
                   **dict.fromkeys("MN", "5"), "R": "6"}
        digits = [mapping.get(c, "") for c in tail]
        out = [first]
        prev = mapping.get(first, "")
        for d in digits:
            if d and d != prev:
                out.append(d)
            prev = d if d else prev
        code = "".join(c for c in out if c)[:4]
        return (code + "000")[:4]

    @classmethod
    def phonetic_equal(cls, a: str, b: str) -> bool:
        return cls.soundex(a) == cls.soundex(b)

    # --------------------------------------------------------------- token/jaccard
    @staticmethod
    def _tokenize(s: str) -> set[str]:
        return set(_NON_ALNUM.sub(" ", s.lower()).split())

    @classmethod
    def jaccard(cls, a: str, b: str) -> float:
        ta, tb = cls._tokenize(a or ""), cls._tokenize(b or "")
        if not ta and not tb:
            return 100.0
        if not ta or not tb:
            return 0.0
        inter = len(ta & tb)
        union = len(ta | tb)
        return 100.0 * inter / union

    @staticmethod
    def ngrams(s: str, n: int = 3) -> set[str]:
        s = f"  {s.lower()}  "
        return {s[i:i + n] for i in range(len(s) - n + 1)}

    @classmethod
    def ngram_similarity(cls, a: str, b: str, n: int = 3) -> float:
        na, nb = cls.ngrams(a or "", n), cls.ngrams(b or "", n)
        if not na and not nb:
            return 100.0
        if not na or not nb:
            return 0.0
        return 100.0 * len(na & nb) / len(na | nb)
