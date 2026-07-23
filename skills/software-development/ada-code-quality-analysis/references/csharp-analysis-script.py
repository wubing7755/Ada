# C# Code Quality Analysis Script (Reference Implementation)
#
# This is the reference script used in the Atlas 2026-07-20 analysis session.
# Adapt regex patterns and thresholds for other languages.
#
# Usage: Call from execute_code or adapt for terminal use.
# Output: Prints complexity, duplication, security, dependency, and standards findings.

import os
import re
from collections import defaultdict, Counter

# === CONFIGURATION ===
SRC = r"<PROJECT_ROOT>/src/<MAIN_MODULE>"   # Adjust per project
EXCLUDE_DIRS = {'obj', 'bin', 'node_modules'}
EXCLUDE_FILES = {'AssemblyInfo.cs', 'GlobalUsings.g.cs'}

# === FILE DISCOVERY ===
def discover_files(sources):
    cs_files = []
    for d, _, fs in os.walk(sources):
        if any(ex in d for ex in EXCLUDE_DIRS):
            continue
        for f in fs:
            if f.endswith('.cs') and not any(ex in f for ex in EXCLUDE_FILES):
                cs_files.append(os.path.join(d, f))
    return cs_files

# === COMPLEXITY: Cyclomatic Complexity Estimation ===
def estimate_cc(text):
    """Quick CC estimate: count branching keywords"""
    cc = 1
    cc += len(re.findall(r'\bif\s*\(', text))
    cc += len(re.findall(r'\belse\s+if\b', text))
    cc += len(re.findall(r'\bcase\s+', text))
    cc += len(re.findall(r'\bfor\s*\(', text))
    cc += len(re.findall(r'\bforeach\s*\(', text))
    cc += len(re.findall(r'\bwhile\s*\(', text))
    cc += len(re.findall(r'\bcatch\s*\(', text))
    cc += len(re.findall(r'&&', text))
    cc += len(re.findall(r'\|\|', text))
    cc += len(re.findall(r'\?\s*\w', text))  # ternaries
    return cc

def extract_methods(filepath):
    """Extract methods with brace-counting bounds"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    methods = []
    current_method = None
    brace_depth = 0
    in_method = False
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('[') or stripped.startswith('#'):
            continue
        
        method_match = re.match(
            r'^\s*(public|private|protected|internal|static|\s)+[\w<>\[\],\s]+\s+(\w+)\s*\([^)]*\)\s*(\{|=>|;)?',
            stripped
        )
        
        if method_match and not in_method and not stripped.startswith('class ') and not stripped.startswith('struct ') and not stripped.startswith('enum ') and not stripped.startswith('interface '):
            name = method_match.group(2)
            has_brace = method_match.group(3) == '{' or (i < len(lines) and '{' in lines[i])
            has_arrow = method_match.group(3) == '=>' or '=>' in stripped
            has_semicolon = method_match.group(3) == ';' or stripped.rstrip().endswith(';')
            
            if has_brace or has_arrow or not has_semicolon:
                current_method = {'name': name, 'start': i}
                in_method = True
                brace_depth = 0
        
        if in_method:
            brace_depth += line.count('{') - line.count('}')
            if brace_depth <= 0 and i > current_method.get('start', 0):
                current_method['end'] = i
                current_method['lines'] = i - current_method['start'] + 1
                method_lines = lines[current_method['start']-1:i]
                current_method['cc'] = estimate_cc(''.join(method_lines))
                methods.append(current_method)
                in_method = False
                current_method = None
    
    return lines, methods

def analyze_complexity(cs_files):
    """Returns: high_cc (CC>10), long_methods (>50 lines), large_classes (>300 lines), deep_nesting"""
    all_methods = []
    large_classes = []
    deep_nesting = []
    
    for f in cs_files:
        lines, methods = extract_methods(f)
        rel = os.path.relpath(f, SRC)
        lc = len(lines)
        if lc > 300:
            large_classes.append((rel, lc))
        
        for m in methods:
            m['file'] = rel
            all_methods.append(m)
        
        # Nesting depth
        max_depth, current_depth, max_line = 0, 0, 0
        for i, line in enumerate(lines, 1):
            current_depth += line.count('{') - line.count('}')
            if current_depth > max_depth:
                max_depth = current_depth
                max_line = i
        if max_depth > 4:
            deep_nesting.append((rel, max_depth, max_line))
    
    high_cc = sorted([m for m in all_methods if m['cc'] > 10], key=lambda x: -x['cc'])
    long_methods = sorted([m for m in all_methods if m['lines'] > 50], key=lambda x: -x['lines'])
    deep_nesting.sort(key=lambda x: -x[1])
    
    return high_cc, long_methods, large_classes, deep_nesting

# === DUPLICATION: 5-line sliding window ===
def analyze_duplication(cs_files, block_size=5):
    all_blocks = []
    for f in cs_files:
        with open(f, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()
        rel = os.path.relpath(f, SRC)
        for i in range(len(lines) - block_size + 1):
            block = tuple(line.strip() for line in lines[i:i+block_size])
            meaningful = any(l and not l.startswith('//') and l not in ('{', '}', '') for l in block)
            if meaningful:
                all_blocks.append((block, rel, i+1))
    
    block_counter = Counter(b[0] for b in all_blocks)
    dupes = sorted([(block, count) for block, count in block_counter.items() if count > 1], key=lambda x: -x[1])
    return dupes

# === SECURITY ===
def analyze_security(cs_files):
    findings = {
        'secrets': [],
        'xss': [],
        'insecure_deser': [],
        'empty_catch': [],
        'generic_exception': [],
        'path_traversal': []
    }
    
    for f in cs_files:
        with open(f, 'r', encoding='utf-8') as fh:
            text = fh.read()
        rel = os.path.relpath(f, SRC)
        
        # Hardcoded secrets
        for m in re.finditer(r'(password|secret|apikey|api_key|token|connectionstring)\s*=\s*"[^"]+"', text, re.IGNORECASE):
            findings['secrets'].append((rel, text[:m.start()].count('\n') + 1, m.group()))
        
        # XSS
        for m in re.finditer(r'MarkupString|\.InnerHtml\b|Html\.Raw\b|@\(\(MarkupString\)', text):
            findings['xss'].append((rel, text[:m.start()].count('\n') + 1))
        
        # Insecure deserialization
        if 'BinaryFormatter' in text or 'SoapFormatter' in text or 'NetDataContractSerializer' in text:
            findings['insecure_deser'].append(rel)
        
        # Empty catch
        for m in re.finditer(r'catch\s*\([^)]*\)\s*\{\s*\}', text):
            findings['empty_catch'].append((rel, text[:m.start()].count('\n') + 1))
        
        # Generic exception
        for m in re.finditer(r'catch\s*\(\s*Exception\b', text):
            findings['generic_exception'].append((rel, text[:m.start()].count('\n') + 1))
    
    return findings

# === DEPENDENCIES ===
def analyze_dependencies(cs_files):
    deps = defaultdict(set)
    
    for f in cs_files:
        with open(f, 'r', encoding='utf-8') as fh:
            text = fh.read()
        rel = os.path.relpath(f, SRC)
        
        for f2 in cs_files:
            rel2 = os.path.relpath(f2, SRC)
            if rel == rel2:
                continue
            with open(f2, 'r', encoding='utf-8') as fh2:
                text2 = fh2.read()
            for m in re.finditer(r'(?:class|struct|interface|enum|record)\s+(\w+)', text2):
                cls_name = m.group(1)
                if re.search(r'\b' + re.escape(cls_name) + r'\b', text) and cls_name not in ('string', 'int', 'bool', 'void', 'object'):
                    deps[rel].add(rel2)
    
    # Find circular deps
    circular = []
    for f1 in deps:
        for f2 in deps[f1]:
            if f1 in deps.get(f2, set()) and f1 < f2:
                circular.append((f1, f2))
    
    return circular

# === TEST COVERAGE (xUnit/.NET) ===
def analyze_test_coverage(test_dir, src_files_map):
    test_files = []
    for d, _, fs in os.walk(test_dir):
        if any(ex in d for ex in EXCLUDE_DIRS):
            continue
        for f in fs:
            if f.endswith('.cs') and not any(ex in f for ex in EXCLUDE_FILES):
                test_files.append(os.path.join(d, f))
    
    total_tests = 0
    test_summary = []
    for f in test_files:
        with open(f, 'r', encoding='utf-8') as fh:
            text = fh.read()
        count = len(re.findall(r'\[Fact\]|\[Theory\]', text))
        total_tests += count
        test_summary.append((os.path.relpath(f, test_dir), count))
    
    # Map tests to source files (heuristic: TestClassName → ClassName)
    tested = set()
    for f in test_files:
        with open(f, 'r', encoding='utf-8') as fh:
            text = fh.read()
        for cls_full in src_files_map:
            cls_short = cls_full.split('.')[-1]
            if cls_short in text and 'Tests' not in f:
                tested.add(src_files_map[cls_full])
    
    untested = set(src_files_map.values()) - tested
    
    return test_summary, total_tests, tested, untested

# === CODE STANDARDS ===
def analyze_standards(cs_files):
    public_fields = []
    
    for f in cs_files:
        with open(f, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()
        rel = os.path.relpath(f, SRC)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            m = re.match(r'public\s+(?!const|static|class|interface|enum|struct|record|delegate|event)\w+\s+\w+\s+(\w+)\s*[;=]', stripped)
            if m and not stripped.startswith('public override') and '=>' not in stripped:
                if 'readonly' not in stripped and 'partial' not in stripped:
                    public_fields.append((rel, i, stripped[:80]))
    
    return public_fields


# === MAIN RUNNER (call from execute_code) ===
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        SRC = sys.argv[1]
    else:
        # Default: adjust per project
        SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')

    cs_files = discover_files(SRC)
    total_lines = 0
    file_map = {}
    for f in cs_files:
        lc = len(open(f, 'r', encoding='utf-8').readlines())
        total_lines += lc
        file_map[os.path.relpath(f, SRC)] = lc

    print(f"=== FILES: {len(cs_files)} .cs files, {total_lines} total lines ===\n")

    # Complexity
    high_cc, long_methods, large_classes, deep_nesting = analyze_complexity(cs_files)
    print(f"High CC (>10): {len(high_cc)} methods")
    for m in high_cc[:15]:
        print(f"  CC={m['cc']:3d}  lines={m['lines']:3d}  {m['file']}:{m['start']}  {m['name']}()")
    print(f"\nLong methods (>50 lines): {len(long_methods)}")
    for m in long_methods[:15]:
        print(f"  lines={m['lines']:3d}  {m['file']}:{m['start']}  {m['name']}()")
    print(f"\nLarge classes (>300 lines): {len(large_classes)}")
    for f, lc in large_classes:
        print(f"  {lc:4d} lines  {f}")
    print(f"\nDeep nesting (>4): {len(deep_nesting)}")
    for f, d, l in deep_nesting[:10]:
        print(f"  depth={d}  {f}:{l}")

    # Duplication
    dupes = analyze_duplication(cs_files)
    print(f"\nDuplicate blocks (5+ lines, >1 occurrence): {len(dupes)} types")
    for block, count in dupes[:10]:
        print(f"  Appears {count}x: {block[0][:60]}...")

    # Security
    sec = analyze_security(cs_files)
    total_sec = sum(len(v) for v in sec.values())
    print(f"\nSecurity findings: {total_sec}")
    for category, items in sec.items():
        if items:
            print(f"  {category}: {len(items)}")
            for item in items[:5]:
                print(f"    {item}")

    # Dependencies
    circular = analyze_dependencies(cs_files)
    print(f"\nCircular dependencies: {len(circular)} pairs")
    for a, b in circular:
        print(f"  {a} <-> {b}")

    # Test coverage
    test_dir = os.path.join(os.path.dirname(SRC), 'tests')
    if os.path.isdir(test_dir):
        # Build src files map from class definitions
        src_files_map = {}
        for f in cs_files:
            with open(f, 'r', encoding='utf-8') as fh:
                text = fh.read()
            ns_match = re.search(r'namespace\s+([\w.]+)', text)
            ns = ns_match.group(1) if ns_match else ""
            for m in re.finditer(r'(?:class|struct|interface|enum|record)\s+(\w+)', text):
                full_name = f"{ns}.{m.group(1)}" if ns else m.group(1)
                src_files_map[full_name] = os.path.relpath(f, SRC)

        test_summary, total_tests, tested, untested = analyze_test_coverage(test_dir, src_files_map)
        print(f"\nTest files: {len(test_summary)}, test methods: {total_tests}")
        for name, count in test_summary:
            print(f"  {count:3d}  {name}")
        print(f"\nTested source files: {len(tested)}/{len(cs_files)}")
        if untested:
            print(f"Untested: {len(untested)}")
            for u in sorted(untested)[:10]:
                print(f"  {u}")

    # Standards
    public_fields = analyze_standards(cs_files)
    print(f"\nPublic fields (potential anti-pattern): {len(public_fields)}")
    for item in public_fields[:10]:
        print(f"  {item[0]}:{item[1]}: {item[2]}")

    print("\n=== DONE ===")
