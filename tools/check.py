"""One-command check (pre-commit hook): unit tests + text lint.

    python -X utf8 tools/check.py
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
steps = [[sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-t', '.', '-q']]
if (ROOT / 'tools' / 'lint.py').exists():
    steps.append([sys.executable, '-X', 'utf8', 'tools/lint.py'])
for cmd in steps:
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(f'check failed: {" ".join(cmd[3:])}')
print('check ok')
