"""
The prototype template for a python gap-filler.
"""

import json
import re
import subprocess
import sys
from random import choices
from string import ascii_uppercase, digits

test_case_code_template = """
import unittest


{test_case}


{answer}


tests = unittest.defaultTestLoader.loadTestsFromName("__main__")
runner = unittest.TextTestRunner()
result = runner.run(tests)

if result.wasSuccessful():
    print("{secret}")
"""


class TestCase:
    def __init__(self, testcode, **kwargs):
        """
        Construct a testcase from a dictionary representation obtained via JSON
        """
        self.testcode = testcode


def parse_params():
    param_dump = """{{ QUESTION.parameters | json_encode | e('py') }}"""
    defaults = {
        "gapfiller_ui_source": "globalextra",
        "proscribedsubstrings": [],
        "maxfieldlength": 50,
        "is_precheck": "{{ IS_PRECHECK }}" == "1",
    }
    params = defaults | json.loads(param_dump)
    return params


def dump_output_and_quit(mark: float, epilogue: str, exit_code: int = 0):
    outcome = {
        'fraction': mark,
        'testresults': [],
        'epiloguehtml': epilogue,
        'columnformats': [],
        'showdifferences': False
    }
    print(json.dumps(outcome))
    sys.exit(exit_code)


PARAMS = parse_params()
SPLITTER = r"\{\[.*?\]\}"


def parse_testcases():
    testcase_dump = """{{ TESTCASES | json_encode | e('py') }}"""
    return [TestCase(**test) for test in json.loads(testcase_dump)]


def parse_fields():
    answer_dump = """{{ STUDENT_ANSWER | e('py') }}"""
    fields = json.loads(answer_dump)
    max_len = PARAMS["maxfieldlength"]
    if any(len(f) > max_len for f in fields):
        msg = f"Field too long - max field length is {max_len}"
        dump_output_and_quit(0, msg, 1)
    return fields


def fill_gaps(code, fields):
    """
    Replaces the GapFiller replacement fields in the code with the given values.
    """
    segments = re.split(SPLITTER, code)
    prog = segments[0].splitlines(keepends=True)
    for value, segment in zip(fields, segments[1:]):
        value = value.splitlines(keepends=True)
        if len(prog) and len(value) > 1:
            indent = " " * len(prog[-1])
            value = value[0], *(indent + v for v in value[1:])
        prog.extend(value)
        prog.extend(segment.splitlines(keepends=True))
    return "".join(prog)


def parse_answer():
    global_extra_dump = """{{ QUESTION.globalextra | e('py') }}"""
    fields = parse_fields()
    return fill_gaps(global_extra_dump, fields)


def run_one_test(prog):
    with open("prog.py", "w") as src:
        print(prog, file=src)
    try:
        output = subprocess.check_output(
            ["python3", "prog.py"],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
    except subprocess.CalledProcessError as e:
        output = e.output + '\n' if e.output else ''
    return output


def make_test_code(test_case, answer, secret):
    return test_case_code_template.format(
        test_case=test_case, answer=answer, secret=secret
    )


def run_tests():
    answer = parse_answer()
    test = parse_testcases()[0]

    secret = ''.join(choices(ascii_uppercase + digits, k=32))
    testcode = make_test_code(test.testcode, answer, secret)
    output = run_one_test(testcode).strip()

    is_correct = output.endswith(secret)
    message = f"<pre>{output.removesuffix(secret)}</pre>"

    message = f"<h3>{'Success!' if is_correct else 'Incorrect.'}</h3>" + message
    dump_output_and_quit(int(is_correct), message)


run_tests()
