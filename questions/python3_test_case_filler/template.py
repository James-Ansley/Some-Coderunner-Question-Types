"""
The prototype template for a python gap-filler.
"""

import json
import re
import subprocess
import sys


class TestCase:
    def __init__(self, dict_rep):
        """
        Construct a testcase from a dictionary representation obtained via JSON
        """
        self.testcode = dict_rep['testcode']
        self.stdin = dict_rep['stdin']
        self.expected = dict_rep['expected']
        self.extra = dict_rep['extra']
        self.display = dict_rep['display']
        try:
            self.testtype = int(dict_rep['testtype'])
        except:
            self.testtype = 0
        self.hiderestiffail = bool(int(dict_rep['hiderestiffail']))
        self.useasexample = bool(int(dict_rep['useasexample']))
        self.mark = float(dict_rep['mark'])


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


PARAMS = parse_params()
SPLITTER = r"\{\[.*?\]\}"


def parse_testcases():
    testcase_dump = """{{ TESTCASES | json_encode | e('py') }}"""
    return [TestCase(test) for test in json.loads(testcase_dump)]


def parse_fields():
    answer_dump = """{{ STUDENT_ANSWER | e('py') }}"""
    fields = json.loads(answer_dump)
    max_len = PARAMS["maxfieldlength"]
    if any(len(f) > max_len for f in fields):
        outcome = {
            'fraction': 0,
            'testresults': [],
            'epiloguehtml': f"Field too long - max field length is {max_len}",
            'columnformats': [],
            'showdifferences': False
        }
        print(json.dumps(outcome))
        sys.exit(1)
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


def run_one_test(prog, stdin):
    with open("prog.py", "w") as src:
        src.write(prog)
    try:
        output = subprocess.check_output(
            ["python3", "prog.py"],
            input=stdin,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
    except subprocess.CalledProcessError as e:
        output = e.output + '\n' if e.output else ''
    return output


def run_tests():
    test = parse_testcases()[0]
    answer = parse_answer()

    testcode = f"{test.testcode}\n\n{answer}"
    output = run_one_test(testcode, test.stdin)

    is_correct = output.rstrip() == test.expected.rstrip()
    message = "<h3>Success!</h3>" if is_correct else "<h3>Incorrect.</h3>"

    outcome = {
        'fraction': int(is_correct),
        'testresults': [],
        'epiloguehtml': message,
        'columnformats': [],
        'showdifferences': False
    }
    print(json.dumps(outcome))


run_tests()
