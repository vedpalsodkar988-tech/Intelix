import os
import re
import requests
from bs4 import BeautifulSoup

def jobsearch_task(query, user_profile=None):
    """
    AI Job Search - Scrapes Naukri directly for REAL job links
    NO MORE GOOGLE REDIRECTS!
    """
    print(f"💼 AI Job Search Starting...")
    print(f"Original query: {query}")
    
    # Extract the actual role from the query
    clean_query = query.lower()
    
    # Remove these words
    remove_words = [
        'find', 'search', 'get', 'show', 'looking for', 'look for',
        'job', 'jobs', 'position', 'positions', 'for', 'in', 'at',
        'give me', 'get me', 'i want', 'i need', 'opening', 'openings'
    ]
    
    for word in remove_words:
        clean_query = re.sub(r'\b' + word + r'\b', '', clean_query, flags=re.IGNORECASE)
    
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    # Extract location
    location = None
    location_keywords = {
        'pune': 'Pune',
        'mumbai': 'Mumbai',
        'bangalore': 'Bangalore',
        'bengaluru': 'Bangalore',
        'delhi': 'Delhi',
        'hyderabad': 'Hyderabad',
        'chennai': 'Chennai',
        'kolkata': 'Kolkata',
        'remote': 'Remote'
    }
    
    for keyword, city in location_keywords.items():
        if keyword in clean_query:
            location = city
            clean_query = clean_query.replace(keyword, '').strip()
            break
    
    if not clean_query:
        clean_query = "software engineer"
    
    print(f"✅ Searching Naukri for: '{clean_query}'" + (f" in {location}" if location else ""))
    
    # Get API keys
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    
    if not scraperapi_key:
        return {"status": "error", "message": "Search service not configured"}
    
    try:
        # Scrape Naukri directly with BETTER selectors
        jobs = scrape_naukri_better(clean_query, location, scraperapi_key)
        
        if not jobs:
            return {
                "status": "error",
                "message": f"No jobs found for '{clean_query}'. Try keywords like 'software engineer', 'data analyst', 'marketing manager'."
            }
        
        return {
            "status": "success",
            "jobs": jobs[:5],
            "total_found": len(jobs),
            "query": clean_query,
            "location": location or "India",
            "message": f"💼 Found {len(jobs[:5])} jobs for '{clean_query}'!"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": "Job search temporarily unavailable. Please try again."
        }


def scrape_naukri_better(query, location, api_key):
    """
    Scrape Naukri with BETTER method - gets REAL job links!
    """
    jobs = []
    
    try:
        # Build Naukri search URL
        search_term = query.replace(' ', '-')
        
        if location:
            # With location
            location_term = location.lower().replace(' ', '-')
            naukri_url = f"https://www.naukri.com/{search_term}-jobs-in-{location_term}"
        else:
            # Without location
            naukri_url = f"https://www.naukri.com/{search_term}-jobs"
        
        print(f"🔍 Naukri URL: {naukri_url}")
        
        # Use ScraperAPI with premium features
        api_url = f"http://api.scraperapi.com?api_key={api_key}&url={naukri_url}&render=false"
        
        print("⏳ Fetching jobs from Naukri...")
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            print(f"⚠️ Naukri returned status: {response.status_code}")
            return jobs
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # MULTIPLE SELECTOR STRATEGIES
        
        # Strategy 1: Look for article tags with jobTuple class
        job_cards = soup.find_all('article', class_='jobTuple')
        
        if not job_cards:
            # Strategy 2: Look for divs with specific data attributes
            job_cards = soup.find_all('div', attrs={'data-job-id': True})
        
        if not job_cards:
            # Strategy 3: Look for job tuple wrappers
            job_cards = soup.find_all('div', class_='srp-jobtuple-wrapper')
        
        if not job_cards:
            # Strategy 4: Find any article tags
            job_cards = soup.find_all('article')
        
        print(f"📋 Found {len(job_cards)} potential job cards")
        
        for card in job_cards[:15]:  # Process more to ensure we get 5 good ones
            try:
                # Extract title - MULTIPLE ATTEMPTS
                title_elem = None
                title_selectors = [
                    ('a', {'class': 'title'}),
                    ('a', {'class': 'job-title'}),
                    ('h2', {}),
                    ('a', {'title': True}),
                    ('div', {'class': 'title'})
                ]
                
                for tag, attrs in title_selectors:
                    title_elem = card.find(tag, attrs)
                    if title_elem:
                        break
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Skip if title is too short or generic
                if len(title) < 5:
                    continue
                
                # Extract link - CRITICAL!
                link = None
                if title_elem.get('href'):
                    href = title_elem['href']
                    if href.startswith('http'):
                        link = href
                    elif href.startswith('/'):
                        link = f"https://www.naukri.com{href}"
                
                # Skip if no proper link
                if not link or 'naukri.com' not in link:
                    continue
                
                # Extract company
                company_elem = None
                company_selectors = [
                    ('a', {'class': 'subTitle'}),
                    ('div', {'class': 'companyInfo'}),
                    ('span', {'class': 'comp-name'})
                ]
                
                for tag, attrs in company_selectors:
                    company_elem = card.find(tag, attrs)
                    if company_elem:
                        break
                
                company = company_elem.get_text(strip=True) if company_elem else "Company"
                
                # Extract experience
                exp_elem = card.find('li', class_='experience') or card.find('span', class_='expwdth')
                experience = exp_elem.get_text(strip=True) if exp_elem else "0-3 years"
                
                # Extract salary
                sal_elem = card.find('li', class_='salary') or card.find('span', class_='sal')
                salary = sal_elem.get_text(strip=True) if sal_elem else "Not disclosed"
                
                # Extract location
                loc_elem = card.find('li', class_='location') or card.find('span', class_='loc')
                job_location = loc_elem.get_text(strip=True) if loc_elem else (location or "India")
                
                job = {
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "salary": salary,
                    "experience": experience,
                    "link": link,
                    "source": "Naukri"
                }
                
                jobs.append(job)
                print(f"✅ {title} at {company} -> {link[:50]}...")
                
                # Stop once we have enough jobs
                if len(jobs) >= 5:
                    break
                
            except Exception as e:
                print(f"⚠️ Error parsing job card: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"❌ Naukri scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return jobs
