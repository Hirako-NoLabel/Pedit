"""Conservative release-content gate, not a guarantee of secret detection."""
from pathlib import Path
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.ruff_cache', 'build', 'dist'}
FORBIDDEN = {'.pdf', '.pem', '.key', '.pyc', '.pyo', '.ttf', '.otf', '.ttc', '.woff', '.woff2', '.onnx', '.exe', '.dll', '.png', '.jpg', '.jpeg'}
PATTERNS = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'provider-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9]{32,})'),
    'personal-absolute-path': re.compile(r'(?:[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\s]+|/(?:Users|home|mnt/data)/[^\s]+)', re.I),
    'assigned-secret': re.compile(r'''(?i)(?:api[_-]?key|client[_-]?secret|password|access[_-]?token)\s*[:=]\s*["'][A-Za-z0-9_+/=-]{16,}["']'''),
    'retired-identifier': re.compile(r'\b(?:LH[-]K|MO[D]EL|DE[M]O)-(?:100|600|700)\b', re.I),
}


def main():
    failures = []
    count = 0
    for directory in ('examples', 'demo', 'demos'):
        if (ROOT / directory).exists():
            failures.append(f'{directory}: publication sample directory is not allowed')
    metadata = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
    if not re.search(r'^license = "AGPL-3.0-or-later"$', metadata, re.M):
        failures.append('Project license metadata must be AGPL-3.0-or-later')
    license_bytes = (ROOT / 'LICENSE').read_bytes().replace(b'\r\n', b'\n')
    # Checked against the unmodified GNU agpl-3.0.txt distribution text.
    if hashlib.sha256(license_bytes).hexdigest() != '0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0':
        failures.append('LICENSE must contain the standard GNU AGPL v3 text')
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT)
        if any(x in IGNORED or x.endswith('.egg-info') for x in rel.parts):
            continue
        if p.is_symlink():
            failures.append(f'{rel}: symlink')
        if not p.is_file():
            continue
        count += 1
        if p.name.startswith('.env') or p.suffix.lower() in FORBIDDEN:
            failures.append(f'{rel}: prohibited release asset')
        try:
            text = p.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            failures.append(f'{rel}: unreviewed binary')
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                failures.append(f'{rel}: {label} (value intentionally omitted)')
    if failures:
        print('\n'.join(failures))
        return 1
    print(f'PASS: {count} release files checked; no PDF assets; AGPL metadata/text verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
