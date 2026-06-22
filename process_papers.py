#!/usr/bin/env python3
import re
import os
from collections import defaultdict

REPO_ROOT = "/home/baru/sc-workspace/10160_20260621220300/10160_20260621220300_benedekrozemberczki_awesome-graph-classification"
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
    return re.sub(r'\s*\([^)]*\d{4}\s*\)\s*$', '', title).strip()

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
    seen_titles = {}
    unique_papers = []
    
    arxiv_versions = defaultdict(list)
    for paper in all_papers:
        for aid in paper["arxiv_ids"]:
            base_id = normalize_arxiv_id(aid)
            version = get_arxiv_version(aid)
            arxiv_versions[base_id].append((version, aid, paper))
    
    removed_arxiv_papers = set()
    for base_id, entries in arxiv_versions.items():
        if len(entries) > 1:
            titles = set(e[2]["title"].lower() for e in entries)
            if titles.issubset(PAPERS_TO_KEEP_BOTH) and len(titles) == 2:
                continue
            
            is_propagation = all("propagation kernel" in e[2]["title"].lower() for e in entries)
            if is_propagation:
                entries.sort(key=lambda x: (x[2]["year"], x[0]), reverse=True)
                kept_paper = None
                for v, a, p in entries:
                    if "Marion Neumann, Roman Garnett" in p["authors_raw"]:
                        kept_paper = p
                        break
                if kept_paper is None:
                    kept_paper = entries[0][2]
                
                for v, a, p in entries:
                    if id(p) != id(kept_paper):
                        duplicates_found.append({
                            "title": p["title"],
                            "reason": f"Same title/link (Propagation Kernels), kept correct version in {kept_paper['year']}",
                            "kept_in": kept_paper["source_file"],
                            "removed_from": p["source_file"]
                        })
                        removed_arxiv_papers.add(id(p))
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
                    removed_arxiv_papers.add(id(paper))
    
    for paper in all_papers:
        title_key = paper["title"].lower().strip()
        
        if id(paper) in removed_arxiv_papers:
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
            continue
        
        seen_titles[title_key] = paper
        unique_papers.append(paper)
    
    return unique_papers

def process_papers():
    all_papers = []
    file_headers = {}
    
    for filename in FILES:
        filepath = os.path.join(CHAPTERS_DIR, filename)
        papers, category_header = parse_file(filepath)
        all_papers.extend(papers)
        file_headers[filename] = category_header
    
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
    
    papers_by_file = defaultdict(lambda: defaultdict(list))
    for paper in unique_papers:
        papers_by_file[paper["source_file"]][paper["year"]].append(paper)
    
    for filename in papers_by_file:
        for year in papers_by_file[filename]:
            papers_by_file[filename][year].sort(key=lambda p: p["title"].lower())
    
    return papers_by_file, file_headers

def format_paper_markdown(paper):
    lines = []
    
    if paper["venue"]:
        full_title = f"**{paper['title']} ({paper['venue']} {paper['year']})**"
    else:
        full_title = f"**{paper['title']} ({paper['year']})**"
    
    lines.append(f"- {full_title}")
    
    if paper["authors"]:
        lines.append(f"  - {paper['authors']}")
    
    for link_text, link_url in paper["links"]:
        lines.append(f"  - [[{link_text}]]({link_url})")
    
    return "\n".join(lines)

def strip_trailing_whitespace(text):
    lines = text.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    return '\n'.join(cleaned_lines)

def process_readme():
    readme_path = os.path.join(REPO_ROOT, "README.md")
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'sindresorhus/awesome' in line and '[![Awesome]' in line:
            lines[i] = '[![Awesome](https://raw.githubusercontent.com/benedekrozemberczki/awesome-graph-classification/master/media/badge.svg)](https://github.com/benedekrozemberczki/awesome-graph-classification)'
            break
    
    content = '\n'.join(lines)
    
    new_contents = """## Contents  

1. [Matrix Factorization](https://github.com/benedekrozemberczki/awesome-graph-classification/blob/master/chapters/matrix_factorization.md)  
2. [Spectral and Statistical Fingerprints](https://github.com/benedekrozemberczki/awesome-graph-classification/blob/master/chapters/fingerprints.md)
3. [Deep Learning](https://github.com/benedekrozemberczki/awesome-graph-classification/blob/master/chapters/deep_learning.md)  
4. [Graph Kernels](https://github.com/benedekrozemberczki/awesome-graph-classification/blob/master/chapters/kernels.md)
5. [License](https://github.com/benedekrozemberczki/awesome-graph-classification/blob/master/LICENSE)
6. [Contributing Guidelines](https://github.com/benedekrozemberczki/awesome-graph-classification/blob/master/contributing.md)
7. [Code of Conduct](https://github.com/benedekrozemberczki/awesome-graph-classification/blob/master/code-of-conduct.md)
8. [Project Logo](https://github.com/benedekrozemberczki/awesome-graph-classification/blob/master/atlas.png)
"""
    
    content = re.sub(
        r'## Contents\s*\n\n.*?(?=\n---+\n)',
        new_contents + '\n',
        content,
        flags=re.DOTALL
    )
    
    content = strip_trailing_whitespace(content)
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Updated README.md: badge and Contents section")

def process_auxiliary_files():
    aux_files = [
        os.path.join(REPO_ROOT, "LICENSE"),
        os.path.join(REPO_ROOT, "contributing.md"),
        os.path.join(REPO_ROOT, "code-of-conduct.md")
    ]
    
    for filepath in aux_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = strip_trailing_whitespace(content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Cleaned trailing whitespace: {os.path.basename(filepath)}")

def delete_awesome_py():
    awesome_py_path = os.path.join(REPO_ROOT, "awesome.py")
    if os.path.exists(awesome_py_path):
        os.remove(awesome_py_path)
        print("✓ Deleted awesome.py")
    
    md_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        if '.git' in dirs:
            dirs.remove('.git')
        for file in files:
            if file.endswith('.md') or file.endswith('.py'):
                md_files.append(os.path.join(root, file))
    
    found_refs = []
    for filepath in md_files:
        if filepath.endswith('process_papers.py'):
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'awesome.py' in content:
            found_refs.append(filepath)
    
    if found_refs:
        print(f"WARNING: Found references to awesome.py in: {found_refs}")
    else:
        print("✓ Verified no remaining references to awesome.py")

def generate_output(papers_by_file, file_headers):
    output_files = {}
    
    for filename in sorted(papers_by_file.keys()):
        header = file_headers.get(filename, "## Unknown")
        years = sorted(papers_by_file[filename].keys(), reverse=True)
        
        content_lines = [header, ""]
        
        for year_idx, year in enumerate(years):
            if year_idx > 0:
                content_lines.append("")
            content_lines.append(f"### {year}")
            content_lines.append("")
            
            for paper_idx, paper in enumerate(papers_by_file[filename][year]):
                content_lines.append(format_paper_markdown(paper))
                if paper_idx < len(papers_by_file[filename][year]) - 1:
                    content_lines.append("")
        
        while content_lines and content_lines[-1] == "":
            content_lines.pop()
        
        output_files[filename] = "\n".join(content_lines)
    
    for filename, content in output_files.items():
        filepath = os.path.join(CHAPTERS_DIR, filename)
        content = strip_trailing_whitespace(content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Wrote {filename}")
    
    return output_files

def print_summary():
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    
    if year_corrections:
        print(f"\nYear Corrections ({len(year_corrections)}):")
        for corr in year_corrections:
            print(f"  - '{corr['title']}': {corr['section_year']} -> {corr['venue_year']} (in {corr['file']})")
    
    if duplicates_found:
        print(f"\nDuplicates Removed ({len(duplicates_found)}):")
        for dup in duplicates_found:
            print(f"  - '{dup['title']}': {dup['reason']}")
            print(f"    Kept in: {dup['kept_in']}, Removed from: {dup['removed_from']}")
    
    if author_fixes:
        print(f"\nAuthor Format Fixes ({len(author_fixes)}):")
        seen = set()
        for fix in author_fixes:
            key = (fix['original'], fix['cleaned'])
            if key not in seen:
                seen.add(key)
                print(f"  - '{fix['original']}' -> '{fix['cleaned']}'")
    
    print("\n" + "="*60)

def main():
    print("="*60)
    print("AWESOME GRAPH CLASSIFICATION - PAPER LIST CLEANUP")
    print("="*60 + "\n")
    
    papers_by_file, file_headers = process_papers()
    generate_output(papers_by_file, file_headers)
    process_readme()
    process_auxiliary_files()
    delete_awesome_py()
    print_summary()
    
    total_papers = sum(len(papers) for file_data in papers_by_file.values() for papers in file_data.values())
    print(f"\n✓ Total papers after cleanup: {total_papers}")
    print(f"✓ Year corrections: {len(year_corrections)}")
    print(f"✓ Duplicates removed: {len(duplicates_found)}")
    print(f"✓ Author fixes: {len(author_fixes)}")
    print("\n✓ All processing complete!")

if __name__ == "__main__":
    main()
