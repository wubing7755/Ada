# Quick Survey Commands

## Count occurrences of a term
```sh
grep -c 'TERM' SRS.md
```

## Count occurrences of multiple old terms (should all be 0 after cleanup)
```sh
grep -c 'OLD_A\|OLD_B\|OLD_C' SRS.md
```

## Check for double-pipe table corruption
```sh
grep -n '^||' SRS.md
```

## Check for remaining English labels in SVGs
```sh
grep -n '>Upper<\|>Lower<' SRS.md
```

## Find remaining compound abbreviations after individual replacements
```sh
grep -oP '(Left|Right)\s*Dock\s+(Upper|Lower)?' SRS.md | sort | uniq -c
```

## Targeted sed replacement on specific line numbers
```sh
# Always verify line numbers first (previous patches may shift lines)
grep -n 'PATTERN' SRS.md
sed -i '999s/OLD/NEW/' SRS.md
```

## Escape-safe SVG text replacement (when quotes cause patch-tool issues)
```sh
# Use sed with exact line number, no quote escaping needed
sed -i '511s/>Upper</>中文替换</' SRS.md
```
