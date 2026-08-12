#!/usr/bin/env python3
"""Parse .trx test results for reliable pass/fail counts.

Why: on zh-CN Windows the dotnet console output is GBK mojibake and grepping
it for 'Passed!/已通过' misses; the TRX file is the machine-readable source.
Note: the TRX root is namespaced, so ET.iter('Counters') matches nothing —
count UnitTestResult/@outcome instead.

Usage:
    dotnet test <sln> --logger "trx;LogFileName=verify.trx"
    python parse-trx.py tests/*/TestResults/verify.trx
    python parse-trx.py <dir>            # globs tests/*/TestResults/verify.trx

Exit code 0 if zero failures.
"""
import glob
import sys
import xml.etree.ElementTree as ET

NS = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
OUTCOME_ATTR = "outcome"


def count(filepath: str):
    root = ET.parse(filepath).getroot()
    passed = failed = total = 0
    for r in root.findall(".//t:UnitTestResult", NS):
        total += 1
        out = r.get(OUTCOME_ATTR)
        if out == "Passed":
            passed += 1
        elif out == "Failed":
            failed += 1
            print(f"FAIL: {r.get('testName')}")
    return passed, failed, total


def main(argv):
    files = []
    for arg in argv:
        if "*" in arg or "/" in arg and not arg.endswith(".trx"):
            files.extend(glob.glob(arg))
        else:
            files.append(arg)
    if not files:
        files = glob.glob("tests/*/TestResults/verify.trx")
    if not files:
        print("no trx files found", file=sys.stderr)
        return 2

    passed = failed = total = 0
    for f in files:
        p, fa, t = count(f)
        passed += p
        failed += fa
        total += t

    print(f"TRX summary: passed={passed} failed={failed} total={total}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
