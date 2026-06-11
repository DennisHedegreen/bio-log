#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / 'images'
LOGS = ROOT / 'logs'

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.heic'}
SCORES = [
    'Water clarity',
    'Visible life',
    'Smell intensity',
    'Surface activity',
    'Sediment / bottom change',
    'Color shift',
]

MARKDOWN_IMAGE_RE = re.compile(r'!\[([^\]]*)\]\((https?://[^)\s]+)\)')
DIRECT_ATTACHMENT_RE = re.compile(
    r'https://(?:github\.com/user-attachments/assets/[A-Za-z0-9_-]+|private-user-images\.githubusercontent\.com/[^)\s]+)'
)
DATE_RE = re.compile(r'\b(20\d{2}-\d{2}-\d{2})\b')
SECTION_RE_TEMPLATE = r'^##\s+{heading}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)'


@dataclass(frozen=True)
class ImageLink:
    url: str
    suggested_name: str | None = None


def github_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'bio-log-mobile-issue-processor',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


def read_json_url(url: str, token: str | None = None) -> dict:
    request = Request(url, headers=github_headers(token))
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as error:
        raise RuntimeError(f'GitHub API error {error.code}: {error.read().decode("utf-8", errors="replace")}') from error
    except URLError as error:
        raise RuntimeError(f'Could not reach GitHub API: {error}') from error


def write_json_url(url: str, method: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload).encode('utf-8')
    headers = github_headers(token)
    headers['Content-Type'] = 'application/json'
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode('utf-8')
            return json.loads(raw) if raw else {}
    except HTTPError as error:
        raise RuntimeError(f'GitHub API error {error.code}: {error.read().decode("utf-8", errors="replace")}') from error
    except URLError as error:
        raise RuntimeError(f'Could not reach GitHub API: {error}') from error


def fetch_issue(repo: str, issue_number: int, token: str | None) -> dict:
    return read_json_url(f'https://api.github.com/repos/{repo}/issues/{issue_number}', token)


def resolve_entry_date(issue: dict, explicit_date: str | None) -> str:
    if explicit_date:
        return explicit_date

    title = issue.get('title') or ''
    body = issue.get('body') or ''
    for text in (title, body):
        match = DATE_RE.search(text)
        if match:
            return match.group(1)

    if title.strip().lower() == 'today':
        return date.today().isoformat()

    return date.today().isoformat()


def extract_image_links(body: str) -> list[ImageLink]:
    links: list[ImageLink] = []
    seen: set[str] = set()

    for match in MARKDOWN_IMAGE_RE.finditer(body):
        alt_text = match.group(1).strip() or None
        url = match.group(2).strip()
        if url not in seen:
            links.append(ImageLink(url=url, suggested_name=alt_text))
            seen.add(url)

    for match in DIRECT_ATTACHMENT_RE.finditer(body):
        url = match.group(0).strip()
        if url not in seen:
            links.append(ImageLink(url=url))
            seen.add(url)

    return links


def extension_from_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    clean = content_type.split(';', 1)[0].strip().lower()
    mapping = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/webp': '.webp',
        'image/gif': '.gif',
        'image/bmp': '.bmp',
        'image/tiff': '.tiff',
        'image/heic': '.heic',
        'image/heif': '.heic',
    }
    if clean in mapping:
        return mapping[clean]
    guessed = mimetypes.guess_extension(clean)
    if guessed == '.jpe':
        return '.jpg'
    return guessed if guessed in IMAGE_EXTS else None


def extension_from_link(link: ImageLink, content_type: str | None = None) -> str:
    if link.suggested_name:
        suffix = Path(link.suggested_name).suffix.lower()
        if suffix in IMAGE_EXTS:
            return '.jpg' if suffix == '.jpeg' else suffix

    suffix = Path(urlparse(link.url).path).suffix.lower()
    if suffix in IMAGE_EXTS:
        return '.jpg' if suffix == '.jpeg' else suffix

    from_type = extension_from_content_type(content_type)
    return from_type or '.jpg'


def browser_download_headers(url: str, token: str | None = None) -> dict[str, str]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 BioLogProcessor/0.2',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Referer': 'https://github.com/',
    }
    # Do not attach the GitHub token to public github.com/user-attachments URLs.
    # The token is useful for private-user-images.githubusercontent.com URLs.
    if token and 'private-user-images.githubusercontent.com' in url:
        headers['Authorization'] = f'Bearer {token}'
    return headers


def download_candidates(url: str) -> list[str]:
    candidates = [url]
    if 'github.com/user-attachments/assets/' in url and '?' not in url:
        candidates.append(f'{url}?download=1')
    return candidates


def download_with_urlopen(url: str, token: str | None = None) -> tuple[bytes, str | None]:
    request = Request(url, headers=browser_download_headers(url, token))
    with urlopen(request, timeout=60) as response:
        data = response.read()
        content_type = response.headers.get('Content-Type')
        return data, content_type


def download_with_curl(url: str, token: str | None = None) -> tuple[bytes, str | None]:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        output_path = Path(tmp.name)

    headers = browser_download_headers(url, token)
    cmd = [
        'curl',
        '-L',
        '--fail',
        '--silent',
        '--show-error',
        '--retry',
        '3',
        '--output',
        str(output_path),
    ]
    for key, value in headers.items():
        cmd.extend(['-H', f'{key}: {value}'])
    cmd.append(url)

    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    try:
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or '').strip()
            raise RuntimeError(f'curl failed for {url}: {detail or f"exit code {result.returncode}"}')
        data = output_path.read_bytes()
        if not data:
            raise RuntimeError(f'curl downloaded empty file for {url}')
        return data, None
    finally:
        output_path.unlink(missing_ok=True)


def download_image(link: ImageLink, token: str | None = None) -> tuple[bytes, str | None]:
    errors: list[str] = []
    for url in download_candidates(link.url):
        try:
            return download_with_urlopen(url, token)
        except HTTPError as error:
            errors.append(f'urlopen {url}: HTTP {error.code}')
        except URLError as error:
            errors.append(f'urlopen {url}: {error}')
        except Exception as error:
            errors.append(f'urlopen {url}: {error}')

        try:
            return download_with_curl(url, token)
        except Exception as error:
            errors.append(str(error))

    joined = '; '.join(errors)
    raise RuntimeError(f'Could not download image {link.url}. Attempts: {joined}')


def next_image_path(entry_date: str, ext: str) -> Path:
    day_dir = IMAGES / entry_date
    day_dir.mkdir(parents=True, exist_ok=True)
    numbers: list[int] = []
    for path in day_dir.iterdir():
        if not path.is_file():
            continue
        match = re.match(r'(\d+)', path.stem)
        if match:
            numbers.append(int(match.group(1)))
    number = max(numbers) + 1 if numbers else 1
    return day_dir / f'{number:02d}{ext}'


def image_repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def extract_section(body: str, heading: str) -> str:
    pattern = re.compile(SECTION_RE_TEMPLATE.format(heading=re.escape(heading)), re.MULTILINE | re.DOTALL | re.IGNORECASE)
    match = pattern.search(body)
    if not match:
        return ''
    text = match.group('body').strip()
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text).strip()
    return text


def build_new_log(entry_date: str, photo_paths: list[str], issue_body: str, default_score: int) -> str:
    notes = extract_section(issue_body, 'Short notes') or 'Mobile issue intake processed.'
    photos_block = '\n'.join(f'- {path}' for path in photo_paths) if photo_paths else '- none'
    scores_block = '\n'.join(f'- {label}: {default_score}/10' for label in SCORES)
    return f'''# {entry_date}

Scores:
{scores_block}

Photos:
{photos_block}

Short notes:
{notes}

Notable event:
Mobile issue intake processed.
'''


def add_photos_to_existing_log(log_text: str, photo_paths: list[str]) -> str:
    missing = [path for path in photo_paths if path not in log_text]
    if not missing:
        return log_text

    photos_lines = '\n'.join(f'- {path}' for path in missing)
    pattern = re.compile(r'(Photos:\n)(.*?)(\n\n)', re.DOTALL)
    match = pattern.search(log_text)
    if match:
        current = match.group(2).strip()
        if current == '- none':
            replacement_block = photos_lines
        elif current:
            replacement_block = current + '\n' + photos_lines
        else:
            replacement_block = photos_lines
        return log_text[:match.start(2)] + replacement_block + log_text[match.end(2):]

    insertion = f'\nPhotos:\n{photos_lines}\n'
    return log_text.rstrip() + '\n' + insertion + '\n'


def update_or_create_log(entry_date: str, photo_paths: list[str], issue_body: str, create_log: bool, default_score: int) -> Path | None:
    log_path = LOGS / f'{entry_date}.md'
    LOGS.mkdir(parents=True, exist_ok=True)

    if log_path.exists():
        original = log_path.read_text(encoding='utf-8')
        updated = add_photos_to_existing_log(original, photo_paths)
        if updated != original:
            log_path.write_text(updated, encoding='utf-8')
        return log_path

    if create_log:
        log_path.write_text(build_new_log(entry_date, photo_paths, issue_body, default_score), encoding='utf-8')
        return log_path

    return None


def run_git(args: list[str]) -> int:
    return subprocess.run(['git', *args], cwd=ROOT).returncode


def commit_changes(paths: list[Path], message: str, push: bool) -> None:
    if not (ROOT / '.git').exists():
        print('Git repo not initialized here. Skipping commit.')
        return
    rel_paths = [path.relative_to(ROOT).as_posix() for path in paths]
    if run_git(['add', *rel_paths]) != 0:
        raise RuntimeError('git add failed')
    if run_git(['commit', '-m', message]) != 0:
        raise RuntimeError('git commit failed or there was nothing to commit')
    if push and run_git(['push']) != 0:
        raise RuntimeError('git push failed')


def close_issue(repo: str, issue_number: int, token: str) -> None:
    write_json_url(f'https://api.github.com/repos/{repo}/issues/{issue_number}', 'PATCH', {'state': 'closed'}, token)


def comment_on_issue(repo: str, issue_number: int, body: str, token: str) -> None:
    write_json_url(f'https://api.github.com/repos/{repo}/issues/{issue_number}/comments', 'POST', {'body': body}, token)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Process a GitHub mobile Bio Log issue into the normal image archive.')
    parser.add_argument('issue_number', type=int, help='GitHub issue number to process')
    parser.add_argument('--repo', default=os.environ.get('BIO_LOG_REPO', 'DennisHedegreen/bio-log'), help='Repository in owner/name format')
    parser.add_argument('--date', dest='entry_date', help='Entry date. Defaults to YYYY-MM-DD found in issue, title "today", or current date')
    parser.add_argument('--token', default=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN'), help='GitHub token. Defaults to GH_TOKEN or GITHUB_TOKEN')
    parser.add_argument('--create-log', action='store_true', help='Create logs/YYYY-MM-DD.md if it does not already exist')
    parser.add_argument('--default-score', type=int, default=5, choices=range(1, 11), metavar='1-10', help='Default score used only when --create-log creates a new log')
    parser.add_argument('--commit', action='store_true', help='Commit downloaded images and log changes locally')
    parser.add_argument('--push', action='store_true', help='Push after commit')
    parser.add_argument('--close', action='store_true', help='Close the issue after successful processing')
    parser.add_argument('--comment', action='store_true', help='Comment on the issue with processed file paths')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without writing files')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issue = fetch_issue(args.repo, args.issue_number, args.token)
    body = issue.get('body') or ''
    entry_date = resolve_entry_date(issue, args.entry_date)
    links = extract_image_links(body)

    if not links:
        print(f'No GitHub attachment image links found in issue #{args.issue_number}.')
        return 1

    print(f'Processing issue #{args.issue_number} for {entry_date}')
    print(f'Found {len(links)} image link(s).')

    changed_paths: list[Path] = []
    repo_photo_paths: list[str] = []

    for link in links:
        if args.dry_run:
            print(f'DRY RUN: would download {link.url}')
            continue
        data, content_type = download_image(link, args.token)
        ext = extension_from_link(link, content_type)
        target = next_image_path(entry_date, ext)
        target.write_bytes(data)
        changed_paths.append(target)
        repo_path = image_repo_path(target)
        repo_photo_paths.append(repo_path)
        print(f'Saved {repo_path}')

    log_path: Path | None = None
    if not args.dry_run and repo_photo_paths:
        log_path = update_or_create_log(entry_date, repo_photo_paths, body, args.create_log, args.default_score)
        if log_path:
            changed_paths.append(log_path)
            print(f'Updated {log_path.relative_to(ROOT).as_posix()}')
        else:
            print(f'No log updated. Existing log not found and --create-log was not used.')

    if args.commit and not args.dry_run and changed_paths:
        commit_changes(changed_paths, f'Process mobile Bio Log issue #{args.issue_number} for {entry_date}', push=args.push)
        print('Committed changes.' + (' Pushed.' if args.push else ''))

    if args.comment and not args.dry_run and repo_photo_paths:
        if not args.token:
            raise RuntimeError('--comment requires GH_TOKEN/GITHUB_TOKEN or --token')
        comment_on_issue(args.repo, args.issue_number, 'Processed Bio Log intake:\n\n' + '\n'.join(f'- `{path}`' for path in repo_photo_paths), args.token)
        print('Commented on issue.')

    if args.close and not args.dry_run:
        if not args.token:
            raise RuntimeError('--close requires GH_TOKEN/GITHUB_TOKEN or --token')
        close_issue(args.repo, args.issue_number, args.token)
        print('Closed issue.')

    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('\nCancelled.')
        raise SystemExit(130)
    except Exception as error:
        print(f'Error: {error}', file=sys.stderr)
        raise SystemExit(1)
