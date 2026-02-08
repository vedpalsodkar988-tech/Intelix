import os
import re
import requests
from bs4 import BeautifulSoup

def jobsearch_task(query, user_profile=None):
    """
    NAUKRI SCRAPING WITH JAVASCRIPT RENDERING
    TEST VERSION - Uses render=true to load Naukri properly
    """
    print(f"💼 Naukri Job Search (with rendering)...")
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
                print(f"💰 Salary filter: {num_str}+ LPA")
            else:
                min_salary = int(num_str)
            clean_query = re.sub(pattern, '', clean_query, flags=re.IGNORECASE)
            break
    
    # Extract location
    location = None
    location_keywords = {
        'pune': 'Pune', 'mumbai': 'Mumbai', 'bangalore': 'Bangalore',
        'bengaluru': 'Bangalore', 'delhi': 'Delhi', 'hyderabad': 'Hyderabad',
        'chennai': 'Chennai', 'kolkata': 'Kolkata', 'gurgaon': 'Gurgaon',
        'noida': 'Noida', 'remote': 'Remote'
    }
    
    for keyword, city in location_keywords.items():
        if keyword in clean_query:
            location = city
            clean_query = clean_query.replace(keyword, '').strip()
            print(f"📍 Location: {location}")
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
    
    print(f"✅ Searching: '{clean_query}'" + (f" in {location}" if location else ""))
    
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    
    if not scraperapi_key:
        return {"status": "error", "message": "ScraperAPI not configured"}
    
    try:
        # Build Naukri URL
        search_term = clean_query.replace(' ', '-')
        
        if location:
            location_slug = location.lower().replace(' ', '-')
            naukri_url = f"https://www.naukri.com/{search_term}-jobs-in-{location_slug}"
        else:
            naukri_url = f"https://www.naukri.com/{search_term}-jobs"
        
        print(f"🔍 URL: {naukri_url}")
        
        # CRITICAL: render=true to load JavaScript!
        print("📡 Calling ScraperAPI with JavaScript rendering (costs ~7 credits)...")
        scraper_url = f"http://api.scraperapi.com?api_key={scraperapi_key}&url={naukri_url}&render=true"
        
        response = requests.get(scraper_url, timeout=90)  # Rendering takes longer
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Naukri returned {response.status_code}"
            }
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find job cards
        job_cards = (
            soup.find_all('article', class_='jobTuple') or
            soup.find_all('div', class_='srp-jobtuple-wrapper') or
            soup.find_all('div', attrs={'data-job-id': True})
        )
        
        print(f"📋 Found {len(job_cards)} job cards")
        
        if not job_cards:
            # Try alternate selectors after rendering
            job_cards = soup.find_all('div', class_=re.compile(r'job', re.I))
            print(f"📋 Found {len(job_cards)} alternate job elements")
        
        if not job_cards:
            return {
                "status": "error",
                "message": f"Could not find jobs. Naukri structure may have changed. Try: 'software developer', 'data analyst'."
            }
        
        # Extract job details
        jobs = []
        
        for card in job_cards[:10]:
            try:
                # Title
                title_elem = (
                    card.find('a', class_='title') or
                    card.find('a', class_='job-title') or
                    card.find('h2') or
                    card.find('h3')
                )
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Link
                link = None
                if title_elem.name == 'a' and title_elem.get('href'):
                    href = title_elem['href']
                    link = href if href.startswith('http') else f"https://www.naukri.com{href}"
                elif title_elem.find('a'):
                    href = title_elem.find('a')['href']
                    link = href if href.startswith('http') else f"https://www.naukri.com{href}"
                
                if not link or 'naukri.com' not in link:
                    continue
                
                # Company
                company_elem = (
                    card.find('a', class_='subTitle') or
                    card.find('div', class_='companyInfo') or
                    card.find('span', class_='comp-name')
                )
                company = company_elem.get_text(strip=True) if company_elem else "Company"
                
                # Location
                loc_elem = card.find('span', class_='loc') or card.find('li', class_='location')
                job_location = loc_elem.get_text(strip=True) if loc_elem else (location or "India")
                
                # Filter by location
                if location and location.lower() not in job_location.lower():
                    continue
                
                # Salary
                sal_elem = card.find('span', class_='salary') or card.find('li', class_='salary')
                salary = sal_elem.get_text(strip=True) if sal_elem else "Not disclosed"
                
                # Experience
                exp_elem = card.find('span', class_='experience') or card.find('li', class_='experience')
                experience = exp_elem.get_text(strip=True) if exp_elem else "Check job details"
                
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
                print(f"✅ {title} | {company} | {salary}")
                
                if len(jobs) >= 3:  # TOP 3
                    break
                
            except Exception as e:
                print(f"⚠️ Error parsing job: {e}")
                continue
        
        if not jobs:
            return {
                "status": "error",
                "message": "Found job cards but couldn't extract details. Try different keywords."
            }
        
        print(f"🎉 Returning {len(jobs)} jobs!")
        
        return {
            "status": "success",
            "jobs": jobs,
            "total_found": len(jobs),
            "query": clean_query,
            "message": f"💼 Found {len(jobs)} jobs on Naukri!"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}"
        }
