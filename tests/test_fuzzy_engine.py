from bi_platform.engine import FuzzyEngine


def test_ratio_identical():
    fe = FuzzyEngine("ratio")
    assert fe.score("hello", "hello") == 100.0


def test_algorithms_all_return_floats():
    for algo in FuzzyEngine.ALGOS:
        fe = FuzzyEngine(algo)
        assert 0 <= fe.score("Alice Smith", "alice smith") <= 100


def test_best_match_returns_none_below_threshold():
    fe = FuzzyEngine()
    assert fe.best_match("banana", ["apple", "orange"], threshold=90) is None


def test_best_match_returns_when_close():
    fe = FuzzyEngine()
    result = fe.best_match("Alice", ["alice", "bob"], threshold=80)
    assert result is not None
    assert result[0] == "alice"


def test_soundex():
    assert FuzzyEngine.soundex("Robert") == FuzzyEngine.soundex("Rupert")


def test_jaccard_and_ngram_bounds():
    j = FuzzyEngine.jaccard("hello world", "hello world!")
    ng = FuzzyEngine.ngram_similarity("hello", "helli")
    assert 0 <= j <= 100 and 0 <= ng <= 100


def test_phonetic_equal():
    assert FuzzyEngine.phonetic_equal("Smith", "Smyth")
