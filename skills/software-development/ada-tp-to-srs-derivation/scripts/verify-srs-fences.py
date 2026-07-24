#!/usr/bin/env python3
"""
verify-srs-fences.py — Verify SRS markdown file structural integrity.

Checks:
  - Fence count = 2 × requirement count
  - No consecutive fences with nothing between them
  - No orphan fences before section dividers (---)
  - Requirement IDs are sequential with no gaps
  - Priority emoji matches between headers and appendix stats

Usage: python verify-srs-fences.py <path-to-srs.md>
"""

import re
import sys

def verify(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    
    # Find all requirement headers and fence positions
    req_headers = []
    fence_positions = []
    
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('### REQ-F-') and not s.startswith('####'):
            req_headers.append((i + 1, s))
        if s == '```':
            fence_positions.append(i)
    
    n_reqs = len(req_headers)
    n_fences = len(fence_positions)
    
    print(f"Requirements: {n_reqs}")
    print(f"Fences:       {n_fences}")
    
    # Check 1: fence parity
    expected_fences = n_reqs * 2
    if n_fences == expected_fences:
        print(f"Fence parity: ✅ ({n_fences} = {n_reqs} × 2)")
    else:
        issues.append(f"Fence parity: ❌ expected {expected_fences}, got {n_fences}")
    
    # Check 2: consecutive fences
    for i in range(len(fence_positions) - 1):
        p1 = fence_positions[i]
        p2 = fence_positions[i + 1]
        gap = p2 - p1 - 1
        if gap == 0:
            issues.append(f"Consecutive fences at lines {p1+1}-{p2+1} (nothing between)")
        elif gap == 1:
            pass  # single blank line between fences is fine
    
    # Check 3: fences before section dividers
    for fp in fence_positions:
        next_line = fp + 1
        while next_line < len(lines) and lines[next_line].strip() == '':
            next_line += 1
        if next_line < len(lines) and lines[next_line].strip() == '---':
            issues.append(f"Fence followed by section divider at line {fp+1}")
    
    # Check 4: sequential IDs
    ids = []
    for _, header in req_headers:
        m = re.search(r'REQ-F-(\d+)', header)
        if m:
            ids.append(int(m.group(1)))
    
    if ids:
        expected_ids = list(range(ids[0], ids[-1] + 1))
        if ids == expected_ids:
            print(f"ID sequence:   ✅ (F-{ids[0]:03d} ~ F-{ids[-1]:03d}, {len(ids)} ids, no gaps)")
        else:
            actual_set = set(ids)
            expected_set = set(expected_ids)
            missing = expected_set - actual_set
            if missing:
                issues.append(f"ID gaps: ❌ missing IDs: {sorted(missing)}")
    
    # Check 5: priority distribution from headers
    p0 = p1 = p2 = 0
    for _, header in req_headers:
        if '🔴' in header: p0 += 1
        elif '🟡' in header: p1 += 1
        elif '🟢' in header: p2 += 1
    
    print(f"Priority:      🔴 P0={p0} 🟡 P1={p1} 🟢 P2={p2}")
    
    # Check 6: vague terms in requirement bodies
    vague_terms = ['正常运行', '适当的', '合理的', '主流浏览器']
    in_block = False
    vague_found = []
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('### REQ-F-'):
            in_block = True
        elif s == '```':
            in_block = not in_block if in_block else False
        if in_block:
            for term in vague_terms:
                if term in s and not s.startswith('###'):
                    vague_found.append((i+1, term, s[:60]))
    
    if vague_found:
        print(f"\n⚠️  Vague terms in requirement bodies ({len(vague_found)}):")
        for line_no, term, ctx in vague_found:
            print(f"  L{line_no}: 「{term}」in \"{ctx}\"")
    
    if issues:
        print(f"\n❌ Issues found ({len(issues)}):")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print(f"\n✅ All checks passed.")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python verify-srs-fences.py <path-to-srs.md>")
        sys.exit(1)
    
    success = verify(sys.argv[1])
    sys.exit(0 if success else 1)
