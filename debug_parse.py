#!/usr/bin/env python3
import re
import os

filepath = 'chapters/kernels.md'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
print(f'Total lines: {len(lines)}')

papers = []
current_year = None
i = 0
while i < len(lines):
    line = lines[i].strip()
    if line.startswith('###'):
        year_match = re.search(r'###\s*(\d{4})', line)
        if year_match:
            current_year = int(year_match.group(1))
            print(f'\nFound year section: {current_year} at line {i}')
        i += 1
        continue
    if line.startswith('- **') and current_year is not None:
        title_match = re.search(r'- \*\*(.+?)\*\*', line)
        if title_match:
            full_title = title_match.group(1).strip()
            print(f'  Paper at line {i}: {full_title[:60]}...')
            papers.append(full_title)
    i += 1

print(f'\nTotal papers found: {len(papers)}')

# Now check what the full script does
print('\n\n=== Checking parse_file function ===')
CHAPTERS_DIR = 'chapters'
filename = 'kernels.md'
filepath = os.path.join(CHAPTERS_DIR, filename)

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
category_header = lines[0].strip() if lines and lines[0].startswith('##') else "## Unknown Category"

print(f'Category header: {category_header}')

papers = []
current_year = None

i = 0
while i < len(lines):
    line = lines[i].strip()
    
    if line.startswith('###'):
        year_match = re.search(r'###\s*(\d{4})', line)
        if year_match:
            current_year = int(year_match.group(1))
            print(f'\nYear section: {current_year}')
        i += 1
        continue
    
    if line.startswith('- **') and current_year is not None:
        title_match = re.search(r'- \*\*(.+?)\*\*', line)
        if title_match:
            full_title = title_match.group(1).strip()
            
            year_match = re.search(r'\(([^)]+)\)', full_title)
            if year_match:
                venue_str = year_match.group(1)
                ym = re.search(r'(\d{4})', venue_str)
                year_from_venue = int(ym.group(1)) if ym else None
            else:
                year_from_venue = None
            
            final_year = year_from_venue if year_from_venue else current_year
            
            if year_from_venue and year_from_venue != current_year:
                print(f'  CORRECTION: {full_title[:50]}: {current_year} -> {year_from_venue}')
            else:
                print(f'  OK: {full_title[:50]}: {final_year}')
            
            papers.append({
                "title": full_title,
                "year": final_year,
                "source_file": filename
            })
    i += 1

print(f'\nTotal papers parsed: {len(papers)}')

# Check by year
from collections import Counter
years = Counter(p['year'] for p in papers)
print('\nPapers by year:')
for y in sorted(years.keys(), reverse=True):
    print(f'  {y}: {years[y]} papers')
