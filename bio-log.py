#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
INCOMING = ROOT / 'incoming'
IMAGES = ROOT / 'images'
LOGS = ROOT / 'logs'

SCORES = [
    ('water_clarity', 'Water clarity', '1 = opaque, 10 = very clear'),
    ('visible_life', 'Visible life', '1 = none visible, 10 = abundant visible activity'),
    ('smell_intensity', 'Smell intensity', '1 = none, 10 = very strong'),
    ('surface_activity', 'Surface activity', '1 = still, 10 = highly active'),
    ('sediment_change', 'Sediment / bottom change', '1 = none, 10 = major visible change'),
    ('color_shift', 'Color shift', '1 = none, 10 = major visible change'),
]

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.heic'}


def prompt(text: str, default: str | None = None) -> str:
    suffix = f' [{default}]' if default else ''
    value = input(f'{text}{suffix}: ').strip()
    return value or (default or '')


def prompt_score(label: str, help_text: str) -> int:
    while True:
        raw = input(f'{label} ({help_text}): ').strip()
        if raw.isdigit() and 1 <= int(raw) <= 10:
            return int(raw)
        print('Enter a whole number from 1 to 10.')


def prompt_yes_no(label: str, default: bool = False) -> bool:
    suffix = '[Y/n]' if default else '[y/N]'
    while True:
        raw = input(f'{label} {suffix}: ').strip().lower()
        if not raw:
            return default
        if raw in {'y', 'yes'}:
            return True
        if raw in {'n', 'no'}:
            return False
        print('Answer y or n.')


def ensure_dirs() -> None:
    for path in (INCOMING, IMAGES, LOGS):
        path.mkdir(parents=True, exist_ok=True)


def list_incoming() -> list[Path]:
    return [p for p in sorted(INCOMING.iterdir()) if p.is_file() and p.name != '.gitkeep']


def list_existing_images(day_dir: Path) -> list[Path]:
    return [p for p in sorted(day_dir.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTS]


def next_image_number(day_dir: Path) -> int:
    existing = list_existing_images(day_dir)
    numbers: list[int] = []
    for path in existing:
        match = re.match(r'(\d+)', path.stem)
        if match:
            numbers.append(int(match.group(1)))
    return (max(numbers) + 1) if numbers else 1


def select_incoming_files(files: list[Path]) -> list[Path]:
    if not files:
        print('\nNo files found in incoming/\n')
        return []
    print('\nFiles found in incoming/:')
    for idx, path in enumerate(files, start=1):
        print(f'  {idx}. {path.name}')
    while True:
        raw = input('Select files for this entry (comma separated, blank for none): ').strip()
        if not raw:
            return []
        try:
            indexes: list[int] = []
            for part in raw.split(','):
                n = int(part.strip())
                if not (1 <= n <= len(files)):
                    raise ValueError
                indexes.append(n)
            deduped: list[Path] = []
            seen: set[int] = set()
            for n in indexes:
                if n not in seen:
                    deduped.append(files[n - 1])
                    seen.add(n)
            return deduped
        except ValueError:
            print('Enter valid numbers like: 1,2,3')


def move_selected_files(entry_date: str, selected: list[Path]) -> list[str]:
    day_dir = IMAGES / entry_date
    day_dir.mkdir(parents=True, exist_ok=True)
    counter = next_image_number(day_dir)
    for source in selected:
        suffix = source.suffix.lower() or '.jpg'
        target = day_dir / f'{counter:02d}{suffix}'
        while target.exists():
            counter += 1
            target = day_dir / f'{counter:02d}{suffix}'
        shutil.move(str(source), str(target))
        counter += 1
    all_images = list_existing_images(day_dir)
    return [f'images/{entry_date}/{path.name}' for path in all_images]


def build_log_text(entry_date: str, scores: dict[str, int], notes: str, notable_event: str, photo_paths: list[str]) -> str:
    photos_block = '- none' if not photo_paths else '\n'.join(f'- {path}' for path in photo_paths)
    notable_block = notable_event if notable_event else 'none'
    return f'''# {entry_date}

Scores:
- Water clarity: {scores['water_clarity']}/10
- Visible life: {scores['visible_life']}/10
- Smell intensity: {scores['smell_intensity']}/10
- Surface activity: {scores['surface_activity']}/10
- Sediment / bottom change: {scores['sediment_change']}/10
- Color shift: {scores['color_shift']}/10

Photos:
{photos_block}

Short notes:
{notes or 'none'}

Notable event:
{notable_block}
'''


def write_log(entry_date: str, text: str) -> Path:
    path = LOGS / f'{entry_date}.md'
    path.write_text(text, encoding='utf-8')
    return path


def show_changed(log_path: Path, photo_paths: list[str]) -> None:
    print('\nChanged files:')
    print(f'  - {log_path.relative_to(ROOT)}')
    for path in photo_paths:
        print(f'  - {path}')


def git_ready() -> bool:
    return (ROOT / '.git').exists()


def run_git(*args: str) -> int:
    return subprocess.run(['git', *args], cwd=ROOT).returncode


def commit_and_push(entry_date: str) -> None:
    if not git_ready():
        print('\nGit repo not initialized here yet. Skipping commit/push.')
        return
    if run_git('add', '.') != 0:
        print('\n`git add .` failed.')
        return
    commit = subprocess.run(['git', 'commit', '-m', f'Log {entry_date}'], cwd=ROOT)
    if commit.returncode != 0:
        print('\nCommit failed or there was nothing new to commit.')
        return
    if run_git('push') != 0:
        print('\n`git push` failed. Your commit is local but not pushed.')
        return
    print('\nGitHub push completed.')


def main() -> int:
    ensure_dirs()
    today = date.today().isoformat()
    print('Bio-Log Entry')
    print()
    entry_date = prompt('Date', today)
    print()
    scores = {key: prompt_score(label, help_text) for key, label, help_text in SCORES}
    print()
    notes = input('Short notes: ').strip()
    print()
    notable_event = ''
    if prompt_yes_no('Notable event today?', default=False):
        notable_event = input('Describe the event briefly: ').strip()
    selected = select_incoming_files(list_incoming())
    photo_paths = move_selected_files(entry_date, selected)
    log_text = build_log_text(entry_date, scores, notes, notable_event, photo_paths)
    log_path = write_log(entry_date, log_text)
    show_changed(log_path, photo_paths)
    print()
    if prompt_yes_no('Commit and push to GitHub now?', default=False):
        commit_and_push(entry_date)
    else:
        print('\nSkipped GitHub push.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
