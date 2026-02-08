import os
import re
import requests
from bs4 import BeautifulSoup

def jobsearch_task(query, user_profile=None):
    """
    DEBUG VERSION - Shows what's happening
    """
    print(f"💼 DEBUG Job Search Starting...")
    print(f"Original query: {query}")
    
    clean_query = query.lower()
    
    # Extract salary
    min_salary = None
    salary_patterns = [
        (r'salary[:\s]+₹?\s*(\d+(?:,\d+)*)\s*\+?', 'absolute'),
        (r'₹\s*(\d+(?:,\d+)*)\s*\+?', 'absolute'),
        (r'(\d+)\s*lpa\s*\+?', 'lpa'),
    ]
    
    for pattern, salary_type in salary_patterns:
        match = re.search(pattern, clean_query, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(',', '')
            if salary_type == 'lpa':
                min_salary = int(num_str) * 100000
            else:
                min_salary = int(num_str)
            clean_query = re.sub(pattern, '', clean_query, flags=re.IGNORECASE)
            break
    
    # Extract location
    location = None
    location_keywords = {
        'pune': 'Pune', 'mumbai': 'Mumbai', 'bangalore': 'Bangalore',
        'bengaluru': 'Bangalore', 'delhi': 'Delhi', 'ncr': 'Delhi NCR',
        'hyderabad': 'Hyderabad', 'chennai': 'Chennai', 'kolkata': 'Kolkata',
        'gurgaon': 'Gurgaon', 'noida': 'Noida', 'remote': 'Remote'
    }
    
    for keyword, city in location_keywords.items():
        if keyword in clean_query:
            location = city
            clean_query = clean_query.replace(keyword, '').strip()
            break
    
    # Clean query
    remove_words = [
        'find', 'search', 'get', 'show', 'looking for', 'look for',
        'job', 'jobs', 'position', 'positions', 'for', 'in', 'at',
        'give me', 'get me', 'i want', 'i need', 'opening', 'openings',
        'salary', 'range', 'lpa', 'per', 'month', 'year', 'annual',
        'minimum', 'above', 'below', 'between'
    ]
    
    for word in remove_words:
        clean_query = re.sub(r'\b' + word + r'\b', '', clean_query, flags=re.IGNORECASE)
    
    clean_query = re.sub(r'[:\-,\+]', ' ', clean_query)
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    if not clean_query:
        clean_query = "software engineer"
    
    print(f"✅ Clean query: '{clean_query}'")
    print(f"📍 Location: {location}")
    
    # Get ScraperAPI key
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    
    if not scraperapi_key:
        return {"status": "error", "message": "ScraperAPI key not configured"}
    
    try:
        # Build Naukri URL
        search_term = clean_query.replace(' ', '-')
        
        if location:
            location_slug = location.lower().replace(' ', '-')
            naukri_url = f"https://www.naukri.com/{search_term}-jobs-in-{location_slug}"
        else:
            naukri_url = f"https://www.naukri.com/{search_term}-jobs"
        
        print(f"🔍 Naukri URL: {naukri_url}")
        
        # Try SIMPLE scraping first (no render)
        print("📡 Calling ScraperAPI...")
        scraper_url = f"http://api.scraperapi.com?api_key={scraperapi_key}&url={naukri_url}"
        response = requests.get(scraper_url, timeout=60)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response size: {len(response.content)} bytes")
        
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Naukri returned status {response.status_code}. URL might be wrong or Naukri is blocking."
            }
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # DEBUG: Save HTML to see what we got
        html_preview = soup.prettify()[:2000]  # First 2000 chars
        print(f"📄 HTML Preview:\n{html_preview}\n")
        
        # Try MULTIPLE selectors
        print("🔍 Trying to find job cards...")
        
        selectors_tried = []
        job_cards = []
        
        # Selector 1
        job_cards = soup.find_all('article', class_='jobTuple')
        selectors_tried.append(f"article.jobTuple → {len(job_cards)} found")
        
        if not job_cards:
            # Selector 2
            job_cards = soup.find_all('div', class_='srp-jobtuple-wrapper')
            selectors_tried.append(f"div.srp-jobtuple-wrapper → {len(job_cards)} found")
        
        if not job_cards:
            # Selector 3
            job_cards = soup.find_all('div', class_='jobTuple')
            selectors_tried.append(f"div.jobTuple → {len(job_cards)} found")
        
        if not job_cards:
            # Selector 4 - ANY article
            job_cards = soup.find_all('article')
            selectors_tried.append(f"article (any) → {len(job_cards)} found")
        
        print(f"📋 Selectors tried:")
        for sel in selectors_tried:
            print(f"  - {sel}")
        
        if not job_cards:
            # Show what tags ARE present
            all_divs = soup.find_all('div', limit=10)
            all_articles = soup.find_all('article', limit=10)
            
            print(f"\n🔍 Found {len(soup.find_all('div'))} total divs")
            print(f"🔍 Found {len(soup.find_all('article'))} total articles")
            
            if all_divs:
                print(f"\n📌 Sample div classes found:")
                for div in all_divs[:5]:
                    classes = div.get('class', [])
                    if classes:
                        print(f"  - {classes}")
            
            return {
                "status": "error",
                "message": f"Could not find job cards on Naukri. Tried {len(selectors_tried)} selectors. Page might have different structure or need JavaScript rendering."
            }
        
        print(f"✅ Found {len(job_cards)} job cards!")
        
        # Try to extract URLs
        job_urls = []
        
        for i, card in enumerate(job_cards[:10]):
            print(f"\n📌 Processing card {i+1}...")
            
            # Try multiple link selectors
            link_elem = (
                card.find('a', class_='title') or
                card.find('a', class_='job-title') or
                card.find('a', attrs={'title': True}) or
                card.find('a', href=re.compile('job-listings'))
            )
            
            if link_elem:
                href = link_elem.get('href', '')
                print(f"  Found link: {href[:80]}...")
                
                if href:
                    if href.startswith('http'):
                        job_url = href
                    elif href.startswith('/'):
                        job_url = f"https://www.naukri.com{href}"
                    else:
                        continue
                    
                    if 'naukri.com' in job_url:
                        job_urls.append(job_url)
                        print(f"  ✅ Added to list")
            else:
                print(f"  ❌ No link found in this card")
        
        print(f"\n🎯 Total job URLs extracted: {len(job_urls)}")
        
        if not job_urls:
            return {
                "status": "error",
                "message": f"Found {len(job_cards)} job cards but could not extract any URLs. Naukri page structure might have changed."
            }
        
        # Return just URLs for now (debug)
        return {
            "status": "success",
            "message": f"DEBUG: Found {len(job_urls)} job URLs",
            "jobs": [
                {
                    "title": f"Job URL {i+1}",
                    "company": "Debug Mode",
                    "location": "See link",
                    "salary": "N/A",
                    "experience": "N/A",
                    "link": url,
                    "source": "Naukri"
                }
                for i, url in enumerate(job_urls[:3])
            ]
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }
