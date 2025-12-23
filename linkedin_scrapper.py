import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import time
import random
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(
    filename=f"linkedin_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_job_ids(keyword, location, limit=50):
    """
    Fast scrape of Job IDs using the 'hidden' guest API.
    """
    job_ids = []
    start = 0
    
    print(f"Collecting job IDs for '{keyword}' in '{location}'...")
    
    while len(job_ids) < limit:
        try:
            params = {
                "keywords": keyword,
                "location": location,
                "start": start,
                "trk": "public_jobs_jobs-search-bar_search-submit"
            }
            
            # This endpoint returns HTML snippets of job cards
            url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            
            if response.status_code != 200:
                logging.error(f"Failed to fetch search page (Status {response.status_code})")
                print(f"⚠ Stopped searching at offset {start}: Status {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("li")
            
            if not job_cards:
                print("No more jobs found.")
                break
                
            new_ids = []
            for card in job_cards:
                # Extract Job ID from the data-entity-urn or link
                # Usually: <div data-entity-urn="urn:li:jobPosting:12345">
                base_card = card.find("div", {"data-entity-urn": True})
                if base_card:
                    entity_urn = base_card.get("data-entity-urn")
                    job_id = entity_urn.split(":")[-1]
                    new_ids.append(job_id)
                else:
                    # Fallback to link extraction
                    link = card.find("a", class_="base-card__full-link")
                    if link:
                        href = link.get("href")
                        # Extract ID from url .../view/12345/...
                        if "view/" in href:
                            job_id = href.split("view/")[1].split("/")[0]
                            new_ids.append(job_id)

            if not new_ids:
                print("Could not extract IDs from current page.")
                break
                
            # Filter duplicates
            unique_new_ids = [jid for jid in new_ids if jid not in job_ids]
            if not unique_new_ids:
                print("No new unique jobs found on this page.")
                break
                
            job_ids.extend(unique_new_ids)
            print(f"  Found {len(unique_new_ids)} new jobs (Total: {len(job_ids)})")
            
            start += 25  # LinkedIn loads 25 jobs per 'page'
            time.sleep(random.uniform(0.5, 1.5)) # Short delay to respect server
            
        except Exception as e:
            logging.error(f"Error searching jobs: {e}")
            print(f"Error: {e}")
            break
            
    return job_ids[:limit]

def get_job_details(job_id):
    """
    Fetch details for a single job ID using the guest API with retries.
    """
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    retries = 4
    
    for attempt in range(retries):
        try:
            # Add random sleep before request to act more human
            time.sleep(random.uniform(1, 6))
            
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 429: # Too Many Requests
                wait_time = (attempt + 2) * 2
                logging.warning(f"Rate limited for {job_id}. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {job_id}: Status {response.status_code}")
                # If it's a 4xx client error (except 429), retrying might not help, but for 5xx/999 we can try
                if response.status_code == 404:
                    return None
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract fields
            title_box = soup.find("div", class_="top-card-layout__entity-info")
            if not title_box:
                # Sometimes we get 200 OK but a login wall / empty page
                if attempt < retries - 1:
                    continue
                return None
                
            title = title_box.find("h2").text.strip() if title_box and title_box.find("h2") else "Unknown"
            
            company_box = title_box.find("h4") if title_box else None
            company = company_box.find("a").text.strip() if company_box and company_box.find("a") else "Unknown"
            
            location_box = title_box.find("div", class_="top-card-layout__first-sub-list") if title_box else None
            location = location_box.find_all("span")[-1].text.strip() if location_box and location_box.find_all("span") else "Unknown"
            
            desc_box = soup.find("div", class_="show-more-less-html__markup")
            description = desc_box.get_text(separator="\n").strip() if desc_box else "No description"
            
            return {
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "link": f"https://www.linkedin.com/jobs/view/{job_id}",
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error fetching details for {job_id} (Attempt {attempt+1}/{retries}): {e}")
            time.sleep(2)
            
    return None

def scrape_linkedin_fast(keywords, location="Indonesia", max_jobs=20):
    """
    Main orchestration function.
    """
    all_jobs = []
    
    # 1. Get IDs first
    for keyword in keywords:
        ids = get_job_ids(keyword, location, limit=max_jobs)
        
        print(f"\nFetching details for {len(ids)} jobs ({keyword})...")
        
        # 2. Fetch details (using threads for speed)
        # Be careful with max_workers to avoid 429 Too Many Requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_id = {executor.submit(get_job_details, jid): jid for jid in ids}
            
            completed_count = 0
            for future in as_completed(future_to_id):
                jid = future_to_id[future]
                try:
                    data = future.result()
                    if data:
                        data["keyword"] = keyword
                        all_jobs.append(data)
                        print(f"✓ Scraped: {data['title'][:40]}...")
                    else:
                        print(f"✗ Failed to get details for {jid}")
                except Exception as exc:
                    print(f"✗ Exception for {jid}: {exc}")
                
                completed_count += 1
                if completed_count % 10 == 0:
                    time.sleep(1) # Slight throttle
                    
    # Save to file
    outfile = "linkedin_jobs.json"
    
    # Check if we should append or overwrite (user asked to reset usually, but let's overwrite for this new file)
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
        
    print(f"\nDone! Saved {len(all_jobs)} jobs to {outfile}")

if __name__ == "__main__":
    print("=== Fast LinkedIn Scraper (Guest API) ===")
    
    kw_input = input("Enter keywords (comma separated) [default: python]: ")
    keywords = [k.strip() for k in kw_input.split(",")] if kw_input.strip() else ["python"]
    
    loc_input = input("Enter location [default: Indonesia]: ")
    location = loc_input.strip() if loc_input.strip() else "Indonesia"
    
    limit = 100
    
    scrape_linkedin_fast(keywords, location, limit)
