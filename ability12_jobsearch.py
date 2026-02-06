import os
import re
import requests
from bs4 import BeautifulSoup

def jobsearch_task(query, user_profile=None):
    """
    AI Job Search - Uses SerpAPI (reliable) with ScraperAPI fallback
    BEST OF BOTH WORLDS!
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
    location = "India"
    location_keywords = {
        'pune': 'Pune, India',
        'mumbai': 'Mumbai, India',
        'bangalore': 'Bangalore, India',
        'bengaluru': 'Bangalore, India',
        'delhi': 'Delhi, India',
        'hyderabad': 'Hyderabad, India',
        'chennai': 'Chennai, India',
        'kolkata': 'Kolkata, India',
        'remote': 'Remote, India'
    }
    
    for keyword, city in location_keywords.items():
        if keyword in clean_query:
            location = city
            clean_query = clean_query.replace(keyword, '').strip()
            break
    
    if not clean_query:
        clean_query = "software engineer"
    
    print(f"✅ Searching for: '{clean_query}' in {location}")
    
    try:
        # METHOD 1: Try SerpAPI first (reliable!)
        serpapi_key = os.environ.get('SERPAPI_KEY', '').strip()
        
        if serpapi_key:
            print("🔍 Using SerpAPI (premium method)...")
            jobs = search_with_serpapi(clean_query, location, serpapi_key)
            
            if jobs:
                print(f"✅ SerpAPI returned {len(jobs)} jobs!")
                return {
                    "status": "success",
                    "jobs": jobs[:5],
                    "total_found": len(jobs),
                    "query": clean_query,
                    "location": location,
                    "message": f"💼 Found {min(5, len(jobs))} jobs for '{clean_query}'!"
                }
        
        # METHOD 2: Fallback to ScraperAPI
        print("🔄 Falling back to ScraperAPI method...")
        scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
        
        if not scraperapi_key:
            return {"status": "error", "message": "Search service not configured"}
        
        jobs = search_with_scraperapi(clean_query, location, scraperapi_key)
        
        if not jobs:
            return {
                "status": "error",
                "message": f"No jobs found for '{clean_query}' in {location}. Try different keywords like 'software engineer', 'data analyst', 'marketing manager'."
            }
        
        return {
            "status": "success",
            "jobs": jobs[:5],
            "total_found": len(jobs),
            "query": clean_query,
            "location": location,
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


def search_with_serpapi(query, location, api_key):
    """
    Search using SerpAPI - Most reliable method!
    """
    jobs = []
    
    try:
        # SerpAPI endpoint for Google Jobs
        url = "https://serpapi.com/search"
        
        params = {
            'engine': 'google_jobs',
            'q': f"{query} {location}",
            'api_key': api_key,
            'hl': 'en',
            'gl': 'in'
        }
        
        print(f"📡 Calling SerpAPI for '{query}' in {location}...")
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"⚠️ SerpAPI status: {response.status_code}")
            return jobs
        
        data = response.json()
        
        # Check if we hit the limit
        if 'error' in data:
            print(f"⚠️ SerpAPI error: {data['error']}")
            return jobs
        
        # Extract jobs from response
        jobs_data = data.get('jobs_results', [])
        
        for job_data in jobs_data[:10]:
            try:
                # Extract extensions (location, type, etc)
                extensions = job_data.get('extensions', [])
                job_type = ', '.join(extensions) if extensions else "Full-time"
                
                # Try to extract salary
                salary_elem = job_data.get('detected_extensions', {})
                salary = salary_elem.get('salary') or salary_elem.get('posted_at') or "Not disclosed"
                
                job = {
                    "title": job_data.get('title', 'Job Opening'),
                    "company": job_data.get('company_name', 'Company'),
                    "location": job_data.get('location', location),
                    "salary": salary,
                    "experience": job_type,
                    "link": job_data.get('share_link') or job_data.get('apply_link'),
                    "source": job_data.get('via', 'Job Board')
                }
                
                jobs.append(job)
                print(f"✅ SerpAPI: {job['title']} at {job['company']}")
                
            except Exception as e:
                print(f"⚠️ Error parsing SerpAPI job: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"❌ SerpAPI failed: {e}")
        return jobs


def search_with_scraperapi(query, location, api_key):
    """
    Fallback: Search using ScraperAPI
    """
    jobs = []
    
    try:
        # Use simple Naukri search
        search_term = query.replace(' ', '-')
        naukri_url = f"https://www.naukri.com/{search_term}-jobs"
        
        print(f"🔍 Scraping Naukri: {naukri_url}")
        
        api_url = f"http://api.scraperapi.com?api_key={api_key}&url={naukri_url}"
        response = requests.get(api_url, timeout=45)
        
        if response.status_code != 200:
            print(f"⚠️ Naukri status: {response.status_code}")
            return jobs
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job cards with multiple selectors
        job_cards = (
            soup.find_all('article', class_='jobTuple') or
            soup.find_all('div', class_='srp-jobtuple-wrapper') or
            soup.find_all('div', class_='jobTupleHeader')
        )
        
        print(f"📋 Found {len(job_cards)} job cards on Naukri")
        
        for card in job_cards[:10]:
            try:
                # Title - try multiple selectors
                title_elem = (
                    card.find('a', class_='title') or
                    card.find('a', class_='job-title') or
                    card.find('h2')
                )
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Company
                company_elem = (
                    card.find('a', class_='subTitle') or
                    card.find('div', class_='companyInfo')
                )
                company = company_elem.get_text(strip=True) if company_elem else "Company"
                
                # Experience
                exp_elem = card.find('li', class_='experience')
                experience = exp_elem.get_text(strip=True) if exp_elem else "0-3 years"
                
                # Salary
                sal_elem = card.find('li', class_='salary')
                salary = sal_elem.get_text(strip=True) if sal_elem else "Not disclosed"
                
                # Location
                loc_elem = card.find('li', class_='location')
                job_location = loc_elem.get_text(strip=True) if loc_elem else location
                
                # Link
                link = None
                if title_elem and title_elem.get('href'):
                    href = title_elem['href']
                    link = href if href.startswith('http') else f"https://www.naukri.com{href}"
                
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
                print(f"✅ Naukri: {title} at {company}")
                
            except Exception as e:
                print(f"⚠️ Error parsing Naukri job: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"❌ ScraperAPI method failed: {e}")
        return jobs

