#!/usr/bin/env python3
"""Verify terminology consistency after specification refactoring.

Usage:
  python3 scripts/verify-terminology.py <spec_file> <old_terms_file>

  old_terms_file: one term per line, each line is the old term to check for.
                  A zero count means the term was successfully replaced.
"""

import sys

def verify(spec_path, old_terms):
    with open(spec_path, encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    all_ok = True
    for term in old_terms:
        count = content.count(term)
        if count > 0:
            # Find the lines where this term appears
            for i, line in enumerate(lines, 1):
                if term in line:
                    print(f"  ✗ Line {i}: {line.strip()[:120]}")
            all_ok = False

    if all_ok:
        print("ALL CLEAN — zero old-term residues")
    else:
        print(f"\nFAIL: old terms still present")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)

    spec_path = sys.argv[1]
    terms_path = sys.argv[2]

    with open(terms_path, encoding='utf-8') as f:
        old_terms = [line.strip() for line in f if line.strip()]

    verify(spec_path, old_terms)
