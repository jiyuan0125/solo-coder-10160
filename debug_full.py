#!/usr/bin/env python3
import re
import os
from collections import defaultdict

REPO_ROOT = "."
CHAPTERS_DIR = os.path.join(REPO_ROOT, "chapters")

FILES = [
    "kernels.md",
    "fingerprints.md",
    "matrix_factorization.md",
    "deep_learning.md"
]

NAME_ORDER_CORRECTIONS = {
    "Vayer Titouan": "Titouan Vayer",
    "Chapel Laetitia": "Laetitia Chapel",
}

PAPERS_TO_KEEP_BOTH = {
    "universal self-attention network for graph classification",
    "unsupervised universal self-attention network for graph classification",
}

duplicates_found = []
year_corrections = []
author_fixes = []

def clean_author(author):
    original = author
    author = author.replace("{", "").replace("}", "")
    author = author.rstrip(";")
    author = author.strip()
    
    if author in NAME_ORDER_CORRECTIONS:
        author = NAME_ORDER_CORRECTIONS[author]
    
    def fix_missing_spaces(match):
        before = match.group(1)
        after = match.group(2)
        if before.lower() == "mc" or before.lower() == "mac" or before.lower() == "o":
            return match.group(0)
        if len(before) == 1:
            return match.group(0)
        if before.lower() == after.lower():
            return match.group(0)
        return f"{before} {after}"
    
    author = re.sub(r'([a-z]+)([A-Z])', fix_missing_spaces, author)
    author = re.sub(r'\s+', ' ', author)
    author = author.strip()
    
    if "," in author and " and " not in author:
        parts = author.split(",", 1)
        if len(parts) == 2:
            surname = parts[0].strip()
            given = parts[1].strip()
            if surname and given and not any(c.isdigit() for c in surname):
                author = f"{given} {surname}"
    
    if author.strip() == "Dinh Phun":
        author = "Dinh Phung"
    if author.strip() == "Karsten M. Borgward":
        author = "Karsten M. Borgwardt"
    if author.strip() == "Karsten Borgward":
        author = "Karsten Borgwardt"
    
    author = re.sub(r'\s+', ' ', author).strip()
    
    if original != author:
        author_fixes.append({
            "original": original,
            "cleaned": author
        })
    return author

def clean_authors(authors_str):
    original = authors_str
    authors_str = authors_str.strip()
    if authors_str.startswith("and "):
        authors_str = authors_str[4:].strip()
    
    authors_str = re.sub(r'\s*,\s*', ', ', authors_str)
    authors_str = re.sub(r'\s+and\s+', ' and ', authors_str)
    
    parts = re.split(r'\s+and\s+', authors_str)
    parts = [p.strip() for p in parts if p.strip()]
    
    all_authors = []
    for part in parts:
        subparts = [sp.strip() for sp in part.split(',') if sp.strip()]
        all_authors.extend(subparts)
    
    cleaned_authors = [clean_author(a) for a in all_authors if a]
    
    if len(cleaned_authors) == 0:
        return ""
    elif len(cleaned_authors) == 1:
        return cleaned_authors[0]
    elif len(cleaned_authors) == 2:
        return f"{cleaned_authors[0]} and {cleaned_authors[1]}"
    else:
        return ", ".join(cleaned_authors[:-1]) + f", and {cleaned_authors[-1]}"

def extract_arxiv_id(link):
    patterns = [
        r'arxiv\.org/(?:abs|pdf)/([\w.-]+)',
        r'arXiv:([\w.-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, link, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def get_arxiv_version(arxiv_id):
    match = re.search(r'v(\d+)$', arxiv_id)
    if match:
        return int(match.group(1))
    return 0

def normalize_arxiv_id(arxiv_id):
    return re.sub(r'v\d+$', '', arxiv_id)

def extract_year_from_venue(title):
    match = re.search(r'\(([^)]+)\)', title)
    if match:
        venue_str = match.group(1)
        year_match = re.search(r'(\d{4})', venue_str)
        if year_match:
            return int(year_match.group(1))
    return None

def extract_venue(title):
    match = re.search(r'\(([^)]+)\)', title)
    if match:
        venue = match.group(1)
        venue = re.sub(r'\s*\d{4}\s*', '', venue).strip()
        return venue
    return None

def clean_title(title):
    return re.sub(r'\s*\([^)]+\d{4}\)\s*$', '', title).strip()

def convert_nips_to_neurips(venue, year, link):
    new_venue = venue
    new_link = link
    
    if year >= 2018:
        if venue and "NIPS" in venue and "NeurIPS" not in venue:
            new_venue = venue.replace("NIPS", "NeurIPS")
        if link and "papers.nips.cc" in link:
            new_link = link.replace("papers.nips.cc", "papers.neurips.cc")
    
    return new_venue, new_link

def fix_link(link):
    if link.startswith("www.bioinf.uni-freiburg.de"):
        return "https://" + link
    return link

def parse_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    category_header = lines[0].strip() if lines and lines[0].startswith('##') else "## Unknown Category"
    
    papers = []
    current_year = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('###'):
            year_match = re.search(r'###\s*(\d{4})', line)
            if year_match:
                current_year = int(year_match.group(1))
            i += 1
            continue
        
        if line.startswith('- **') and current_year is not None:
            title_match = re.search(r'- \*\*(.+?)\*\*', line)
            if title_match:
                full_title = title_match.group(1).strip()
                
                year_from_venue = extract_year_from_venue(full_title)
                venue = extract_venue(full_title)
                clean_title_str = clean_title(full_title)
                
                final_year = year_from_venue if year_from_venue else current_year
                
                if year_from_venue and year_from_venue != current_year:
                    year_corrections.append({
                        "title": clean_title_str,
                        "section_year": current_year,
                        "venue_year": year_from_venue,
                        "file": os.path.basename(filepath)
                    })
                
                authors = ""
                links = []
                j = i + 1
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith('###') or next_line.startswith('- **'):
                        break
                    if next_line.startswith('- '):
                        link_match = re.search(r'\[\[(.+?)\]\]\((.+?)\)', next_line)
                        if link_match:
                            link_text = link_match.group(1)
                            link_url = fix_link(link_match.group(2))
                            links.append((link_text, link_url))
                        else:
                            author_part = next_line.lstrip('- ').strip()
                            if author_part:
                                authors = author_part
                    j += 1
                
                arxiv_ids = []
                for link_text, link_url in links:
                    aid = extract_arxiv_id(link_url)
                    if aid:
                        arxiv_ids.append(aid)
                
                paper = {
                    "title": clean_title_str,
                    "full_title": full_title,
                    "year": final_year,
                    "venue": venue,
                    "authors_raw": authors,
                    "authors": "",
                    "links": links,
                    "arxiv_ids": arxiv_ids,
                    "source_file": os.path.basename(filepath),
                    "category_header": category_header
                }
                
                papers.append(paper)
                i = j - 1
        
        i += 1
    
    return papers, category_header

def remove_duplicates(all_papers):
    print(f"\n=== DEBUG remove_duplicates: input has {len(all_papers)} papers ===")
    
    seen_titles = {}
    unique_papers = []
    
    arxiv_versions = defaultdict(list)
    for paper in all_papers:
        for aid in paper["arxiv_ids"]:
            base_id = normalize_arxiv_id(aid)
            version = get_arxiv_version(aid)
            arxiv_versions[base_id].append((version, aid, paper))
    
    print(f"\n=== DEBUG: arXiv groups ({len(arxiv_versions)}):")
    for base_id, entries in arxiv_versions.items():
        if len(entries) > 1:
            print(f"  {base_id}: {len(entries)} entries")
            for v, a, p in entries:
                print(f"    - v{v}: {p['title'][:40]}... (in {p['source_file']})")
    
    kept_arxiv_papers = set()
    for base_id, entries in arxiv_versions.items():
        if len(entries) > 1:
            titles = set(e[2]["title"].lower() for e in entries)
            if titles.issubset(PAPERS_TO_KEEP_BOTH) and len(titles) == 2:
                print(f"  KEEPING BOTH for {base_id}")
                for v, a, p in entries:
                    kept_arxiv_papers.add(id(p))
                continue
            
            is_propagation = all("propagation kernel" in e[2]["title"].lower() for e in entries)
            if is_propagation:
                print(f"  PROPAGATION KERNELS for {base_id}")
                entries.sort(key=lambda x: (x[2]["year"], x[0]), reverse=True)
                for v, a, p in entries:
                    if "Marion Neumann, Roman Garnett" in p["authors_raw"]:
                        kept_version, kept_aid, kept_paper = v, a, p
                        break
                else:
                    kept_version, kept_aid, kept_paper = entries[0]
                
                for v, a, p in entries:
                    if id(p) != id(kept_paper):
                        duplicates_found.append({
                            "title": p["title"],
                            "reason": f"Same title/link (Propagation Kernels), kept correct version in {kept_paper['year']}",
                            "kept_in": kept_paper["source_file"],
                            "removed_from": p["source_file"]
                        })
                kept_arxiv_papers.add(id(kept_paper))
                continue
            
            entries.sort(key=lambda x: x[0], reverse=True)
            kept_version, kept_aid, kept_paper = entries[0]
            for version, aid, paper in entries[1:]:
                if id(paper) != id(kept_paper):
                    duplicates_found.append({
                        "title": paper["title"],
                        "reason": f"Same arXiv ID {base_id}, kept version v{kept_version} over v{version}",
                        "kept_in": kept_paper["source_file"],
                        "removed_from": paper["source_file"]
                    })
            kept_arxiv_papers.add(id(kept_paper))
        else:
            kept_arxiv_papers.add(id(entries[0][2]))
    
    print(f"\n=== DEBUG: kept_arxiv_papers has {len(kept_arxiv_papers)} IDs")
    
    for paper in all_papers:
        title_key = paper["title"].lower().strip()
        
        if id(paper) not in kept_arxiv_papers:
            print(f"  SKIPPING (arXiv filtered): {paper['title'][:50]}...")
            continue
        
        if title_key in seen_titles:
            existing = seen_titles[title_key]
            if (title_key in PAPERS_TO_KEEP_BOTH and 
                existing["title"].lower() in PAPERS_TO_KEEP_BOTH and
                existing["title"].lower() != title_key):
                unique_papers.append(paper)
                continue
            
            duplicates_found.append({
                "title": paper["title"],
                "reason": "Same title",
                "kept_in": existing["source_file"],
                "removed_from": paper["source_file"]
            })
            print(f"  SKIPPING (title duplicate): {paper['title'][:50]}...")
            continue
        
        seen_titles[title_key] = paper
        unique_papers.append(paper)
    
    print(f"\n=== DEBUG remove_duplicates: output has {len(unique_papers)} papers ===")
    return unique_papers

def process_papers():
    all_papers = []
    file_headers = {}
    
    for filename in FILES:
        filepath = os.path.join(CHAPTERS_DIR, filename)
        papers, category_header = parse_file(filepath)
        print(f"Parsed {len(papers)} papers from {filename}")
        all_papers.extend(papers)
        file_headers[filename] = category_header
    
    print(f"Total papers before dedup: {len(all_papers)}")
    
    for paper in all_papers:
        paper["authors"] = clean_authors(paper["authors_raw"])
        
        new_links = []
        for link_text, link_url in paper["links"]:
            new_venue, new_link = convert_nips_to_neurips(paper["venue"], paper["year"], link_url)
            new_links.append((link_text, new_link))
        paper["links"] = new_links
        if paper["venue"]:
            new_venue, _ = convert_nips_to_neurips(paper["venue"], paper["year"], "")
            paper["venue"] = new_venue
    
    unique_papers = remove_duplicates(all_papers)
    print(f"Total papers after dedup: {len(unique_papers)}")
    
    papers_by_file = defaultdict(lambda: defaultdict(list))
    for paper in unique_papers:
        papers_by_file[paper["source_file"]][paper["year"]].append(paper)
    
    print("\n=== DEBUG: papers_by_file:")
    for filename, year_data in papers_by_file.items():
        total = sum(len(p) for p in year_data.values())
        print(f"  {filename}: {total} papers across years {sorted(year_data.keys(), reverse=True)}")
    
    for filename in papers_by_file:
        for year in papers_by_file[filename]:
            papers_by_file[filename][year].sort(key=lambda p: p["title"].lower())
    
    return papers_by_file, file_headers

def main():
    papers_by_file, file_headers = process_papers()

if __name__ == "__main__":
    main()
