"""
The prototype template for a python gap-filler.
"""

import json
import subprocess
import sys
from random import choices
from string import ascii_uppercase, digits


class TestCase:
    def __init__(self, testcode: str, **kwargs):
        """
        Construct a testcase from a dictionary representation obtained via JSON
        """
        self._testcode = testcode

    def filled_testcode(self, given, then, but):
        given_field = "{[given]}"
        then_field = "{[then]}"
        but_field = "{[but]}"
        code = self._testcode.replace(given_field, given)
        code = code.replace(then_field, then)
        code = code.replace(but_field, but)

        return code


def parse_params():
    param_dump = """{{ QUESTION.parameters | json_encode | e('py') }}"""
    defaults = {
        "gapfiller_ui_source": "globalextra",
        "proscribedsubstrings": [],
        "maxfieldlength": 50,
        "is_precheck": "{{ IS_PRECHECK }}" == "1",
        "cases_must_be_different": True,
    }
    params = defaults | json.loads(param_dump)
    return params


PARAMS = parse_params()
SPLITTER = r"\{\[.*?\]\}"


def chunked(iterable, n):
    args = [iter(iterable)] * n
    return list(zip(*args, strict=True))


def parse_testcases():
    testcase_dump = """{{ TESTCASES | json_encode | e('py') }}"""
    return [TestCase(**test) for test in json.loads(testcase_dump)]


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


def parse_fields():
    answer_dump = """{{ STUDENT_ANSWER | e('py') }}"""
    fields = json.loads(answer_dump)
    max_len = PARAMS["maxfieldlength"]
    if any(len(f) > max_len for f in fields):
        message = f"<p>A field is too long - " \
                  f"max field length is {max_len} chars</p>"
        dump_output_and_quit(0, message, 1)
    return fields


def run_one_test(prog: str) -> str:
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


def run_tests():
    fields = parse_fields()
    cases = chunked(fields, 3)

    tests = parse_testcases()

    is_correct = True
    message = ""

    secret = ''.join(choices(ascii_uppercase + digits, k=32))
    secret_code = f"""\n\n\nprint("{secret}", end='')"""

    for test, case in zip(tests, cases):
        if (PARAMS["cases_must_be_different"]
                and case[1] and case[2]
                and case[1] == case[2]):
            is_correct = False
            message = "The option's output and the actual output must be " \
                      "different to demonstrate that the option is incorrect"
            break

        testcode = test.filled_testcode(*case) + secret_code
        output = run_one_test(testcode).strip()

        if not output == secret:
            is_correct = False
            message = "Some of the cases are not correct"
            break

    message = f"<h3>{'Success!' if is_correct else 'Incorrect.'}</h3>" + message
    dump_output_and_quit(int(is_correct), message)


run_tests()
