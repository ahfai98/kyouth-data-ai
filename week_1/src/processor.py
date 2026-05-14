"""HTML processing module - cleans HTML and extracts structured JSON data."""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError


class JobListing(BaseModel):
    """Pydantic model for job listing data."""
    source_id: str
    job_title: str
    company: str
    description: str
    
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True


def extract_source_id(soup: BeautifulSoup) -> Optional[str]:
    """Extract source_id from og:url meta tag."""
    og_url = soup.find("meta", property="og:url")
    if og_url and og_url.get("content"):
        match = re.search(r'/job/(\d+)', og_url["content"])
        if match:
            return match.group(1)
    return None


def extract_job_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract job title from data-automation attribute."""
    title_elem = soup.find(attrs={"data-automation": "job-detail-title"})
    if title_elem:
        return title_elem.get_text(strip=True)
    
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"]
        title = re.sub(r'\s+Job\s+in\s+.*$', '', title)
        return title.strip()
    
    return None


def extract_company(soup: BeautifulSoup) -> Optional[str]:
    """Extract company name from advertiser-name."""
    company_elem = soup.find("span", attrs={"data-automation": "advertiser-name"})
    if company_elem:
        company = company_elem.get_text(strip=True)
        company = re.sub(r'✓$', '', company).strip()
        return company
    
    company_btn = soup.find("button", attrs={"data-automation": "advertiser-name"})
    if company_btn:
        company = company_btn.get_text(strip=True)
        company = re.sub(r'✓$', '', company).strip()
        return company
    
    return None


def extract_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract job description from jobAdDetails."""
    desc_elem = soup.find("div", attrs={"data-automation": "jobAdDetails"})
    if desc_elem:
        description = desc_elem.get_text(separator="\n", strip=True)
        description = re.sub(r'\n{3,}', '\n\n', description)
        if len(description) > 5000:
            description = description[:5000] + "..."
        return description if len(description) > 50 else None
    
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        return og_desc["content"].strip()
    
    return None


def process_single_html(html_path: Path) -> Tuple[Optional[Dict[str, Any]], bool]:
    """Process a single HTML file and extract job data."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        source_id = extract_source_id(soup)
        job_title = extract_job_title(soup)
        company = extract_company(soup)
        description = extract_description(soup)
        
        # Debug output
        print(f"\n📄 {html_path.name}")
        print(f"   source_id: {source_id}")
        print(f"   job_title: {job_title[:50] if job_title else 'None'}")
        print(f"   company: {company}")
        print(f"   desc_len: {len(description) if description else 0}")
        
        # Check required fields
        if not source_id or not job_title or not company or not description or len(description) < 10:
            print(f"   ❌ Missing required fields")
            return None, False
        
        # Create a dictionary for the data
        raw_data = {
            "source_id": source_id,
            "job_title": job_title,
            "company": company,
            "description": description,
        }
        
        # Use Pydantic for validation only (not for dict conversion)
        try:
            # This validates but we don't use the returned object directly
            JobListing(**raw_data)
            
            # Return the original dictionary (which has all the data)
            print(f"   ✅ VALID - Saving to JSON")
            return raw_data, True
            
        except ValidationError as e:
            print(f"   ❌ Validation error: {e}")
            return None, False
            
    except Exception as e:
        print(f"   ❌ Exception: {type(e).__name__}: {e}")
        return None, False


def process_all_html(input_dir: str, output_dir: str) -> None:
    """Process all HTML files from input_dir to JSON files in output_dir."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        print(f"🥈 Silver: Directory {input_dir} does not exist")
        print(f"\n📊 Silver Summary:\nTotal: 0 | Processed: 0 | Skipped: 0")
        return
    
    html_files = list(input_path.glob("*.html"))
    
    if not html_files:
        print(f"🥈 Silver: No HTML files found in {input_dir}")
        print(f"\n📊 Silver Summary:\nTotal: 0 | Processed: 0 | Skipped: 0")
        return
    
    total = len(html_files)
    processed = 0
    skipped = 0
    
    print(f"🥈 Silver: Processing {total} files...")
    
    for html_file in html_files:
        job_data, is_valid = process_single_html(html_file)
        
        if is_valid and job_data:
            output_file = output_path / f"{html_file.stem}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)
            
            #print(f"   💾 Saved to {output_file.name}")
            processed += 1
        else:
            print(f"⚠️ Skipped {html_file.name} - missing required fields")
            skipped += 1
    
    print(f"\n📊 Silver Summary:")
    print(f"Total: {total} | Processed: {processed} | Skipped: {skipped}")