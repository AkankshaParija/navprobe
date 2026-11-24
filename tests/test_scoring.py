from navprobe.report import parse_answer

YN = ["yes", "no"]
ABC = ["A", "B", "C"]
NUM = ["1", "2", "3", "4"]


def test_parses_plain_json():
    assert parse_answer('{"answer": "yes"}', YN) == "yes"
    assert parse_answer('{"answer": "B"}', ABC) == "B"


def test_normalises_case_and_numbers():
    assert parse_answer('{"answer": "YES"}', YN) == "yes"
    assert parse_answer('{"answer": "b"}', ABC) == "B"
    assert parse_answer('{"answer": 3}', NUM) == "3"
    assert parse_answer('{"answer": "3"}', NUM) == "3"


def test_takes_last_json_and_ignores_reasoning():
    raw = 'Let me think. {"answer": "A"} wait, actually\n```json\n{"answer": "C"}\n```'
    assert parse_answer(raw, ABC) == "C"
    assert parse_answer('<think>{"answer": "no"}</think>{"answer": "yes"}', YN) == "yes"


def test_rejects_invalid_replies():
    assert parse_answer("yes", YN) is None                 # no JSON
    assert parse_answer('{"answer": "maybe"}', YN) is None  # not an allowed choice
    assert parse_answer('{"answer": 7}', NUM) is None
    assert parse_answer("", YN) is None
    assert parse_answer(None, YN) is None
