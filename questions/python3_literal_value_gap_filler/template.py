import ast
import json
from itertools import zip_longest


class FieldTooLong(Exception):
    ...


param_dump = """{{ QUESTION.parameters | json_encode | e('py') }}"""
answer_dump = """{{ STUDENT_ANSWER | e('py') }}"""
testcase_dump = """{{ TESTCASES | json_encode | e('py') }}"""

defaults = {
    "gapfiller_ui_source": "globalextra",
    "proscribedsubstrings": [],
    "maxfieldlength": 50,
}

PARAMS = defaults | json.loads(param_dump)

expect = ast.literal_eval(json.loads(testcase_dump)[0]["testcode"])

try:
    fields = json.loads(answer_dump)
    if any(len(f) > PARAMS["maxfieldlength"] for f in fields):
        raise FieldTooLong

    fields = [ast.literal_eval(f) for f in fields]
except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
    is_correct = False
    message = "<h3>Incorrect.</h3>"

except FieldTooLong:
    is_correct = False
    message = f"Field too long – max {PARAMS['maxfieldlength']} chars"

else:
    is_correct = all(field == ans for field, ans in zip_longest(fields, expect))
    message = "<h3>Success!</h3>" if is_correct else "<h3>Incorrect.</h3>"

outcome = {
    'fraction': int(is_correct),
    'testresults': [],
    'epiloguehtml': message,
    'columnformats': [],
    'showdifferences': False
}

print(json.dumps(outcome))
