import os
import re
import requests
from bs4 import BeautifulSoup

def jobsearch_task(query, user_profile=None):
    """
    NAUKRI-ONLY JOB SEARCH - Uses ONLY ScraperAPI!
    NO SerpAPI needed!
    100% Accurate - scrapes actual job pages!
    """
    print(f"💼 Naukri Job Search Starting...")
    print(f"Original query: {query}")
    
    clean_query = query.lower()
    
    # Extract salary requirements
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
                print(f"💰 Salary filter: ₹{min_salary:,}+")
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
    
    print(f"✅ Searching Naukri for: '{clean_query}'" + (f" in {location}" if location else ""))
    
    # Get ScraperAPI key
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    
    if not scraperapi_key:
        return {"status": "error", "message": "ScraperAPI key not configured"}
    
    try:
        # Build Naukri search URL
        search_term = clean_query.replace(' ', '-')
        
        if location:
            location_slug = location.lower().replace(' ', '-')
            naukri_url = f"https://www.naukri.com/{search_term}-jobs-in-{location_slug}"
        else:
            naukri_url = f"https://www.naukri.com/{search_term}-jobs"
        
        print(f"🔍 Naukri URL: {naukri_url}")
        
        # Scrape Naukri search page
        job_urls = scrape_naukri_search_page(naukri_url, scraperapi_key)
        
        if not job_urls:
            return {
                "status": "error",
                "message": f"No jobs found for '{clean_query}' on Naukri. Try different keywords."
            }
        
        print(f"📋 Found {len(job_urls)} jobs, now scraping each for accurate details...")
        
        # Scrape each job page for accurate details
        verified_jobs = []
        
        for job_url in job_urls:
            if len(verified_jobs) >= 3:  # TOP 3 BEST jobs!
                break
            
            print(f"🔍 Scraping job: {job_url[:60]}...")
            
            job_details = scrape_naukri_job_page(job_url, scraperapi_key, location, min_salary, clean_query)
            
            if job_details:
                verified_jobs.append(job_details)
                print(f"✅ {job_details['title']} | {job_details['salary']} | {job_details['experience']}")
            else:
                print(f"⏭️  Skipped (expired or doesn't match)")
        
        if not verified_jobs:
            return {
                "status": "error",
                "message": f"No active jobs found matching your criteria on Naukri."
            }
        
        print(f"🎉 Returning {len(verified_jobs)} verified Naukri jobs!")
        
        return {
            "status": "success",
            "jobs": verified_jobs,
            "total_found": len(verified_jobs),
            "query": clean_query,
            "message": f"💼 Found {len(verified_jobs)} jobs on Naukri for '{clean_query}'!"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": "Job search failed. Please try again."
        }


def scrape_naukri_search_page(url, api_key):
    """
    Scrape Naukri search page to get job URLs
    """
    job_urls = []
    
    try:
        # Use ScraperAPI
        scraper_url = f"http://api.scraperapi.com?api_key={api_key}&url={url}"
        response = requests.get(scraper_url, timeout=45)
        
        if response.status_code != 200:
            print(f"⚠️ Naukri search page status: {response.status_code}")
            return job_urls
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job cards - multiple selectors for reliability
        job_cards = (
            soup.find_all('article', class_='jobTuple') or
            soup.find_all('div', class_='srp-jobtuple-wrapper') or
            soup.find_all('div', attrs={'data-job-id': True})
        )
        
        print(f"📋 Found {len(job_cards)} job cards on search page")
        
        for card in job_cards[:15]:  # Get up to 15 URLs
            try:
                # Find job link
                link_elem = (
                    card.find('a', class_='title') or
                    card.find('a', class_='job-title') or
                    card.find('h2').find('a') if card.find('h2') else None
                )
                
                if link_elem and link_elem.get('href'):
                    href = link_elem['href']
                    
                    # Make full URL
                    if href.startswith('http'):
                        job_url = href
                    elif href.startswith('/'):
                        job_url = f"https://www.naukri.com{href}"
                    else:
                        continue
                    
                    # Only add valid Naukri job listing URLs
                    if 'naukri.com/job-listings' in job_url:
                        job_urls.append(job_url)
                        print(f"  ✅ Found: {job_url[:60]}...")
                
            except Exception as e:
                print(f"  ⚠️ Error parsing card: {e}")
                continue
        
        return job_urls
        
    except Exception as e:
        print(f"❌ Naukri search scraping failed: {e}")
        return job_urls


def scrape_naukri_job_page(url, api_key, target_location=None, min_salary=None, search_query=None):
    """
    Scrape individual Naukri job page for ACCURATE details
    """
    try:
        # Use ScraperAPI
        scraper_url = f"http://api.scraperapi.com?api_key={api_key}&url={url}"
        response = requests.get(scraper_url, timeout=45)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        
        # CHECK IF EXPIRED
        expired_keywords = ['expired', 'no longer accepting', 'position filled', 'job closed', 'not available']
        if any(word in page_text for word in expired_keywords):
            print("  ⏭️  Job expired")
            return None
        
        # Extract TITLE
        title = "Job Opening"
        title_selectors = [
            soup.find('h1', class_='jd-header-title'),
            soup.find('h1'),
            soup.find('span', class_='styles_jd-header-title'),
        ]
        
        for selector in title_selectors:
            if selector:
                title = selector.get_text(strip=True)
                break
        
        # Extract COMPANY
        company = "Company"
        company_selectors = [
            soup.find('a', class_='comp-name'),
            soup.find('div', class_='company-name'),
            soup.find('a', class_='styles_jd-header-comp-name'),
        ]
        
        for selector in company_selectors:
            if selector:
                company = selector.get_text(strip=True)
                break
        
        # Extract LOCATION
        location = target_location or "India"
        location_selectors = [
            soup.find('span', class_='loc'),
            soup.find('span', class_='location'),
            soup.find('a', class_='styles_jhc__location'),
        ]
        
        for selector in location_selectors:
            if selector:
                loc_text = selector.get_text(strip=True)
                if loc_text:
                    location = loc_text
                    break
        
        # Filter by location if specified
        if target_location:
            if target_location.lower() not in location.lower() and target_location.lower() not in title.lower():
                print(f"  ⏭️  Wrong location: {location} (need {target_location})")
                return None
        
        # Extract SALARY
        salary = "Not disclosed"
        salary_selectors = [
            soup.find('span', class_='salary'),
            soup.find('div', class_='salary-snippet'),
            soup.find('span', class_='styles_jhc__salary'),
        ]
        
        for selector in salary_selectors:
            if selector:
                sal_text = selector.get_text(strip=True)
                if sal_text and len(sal_text) < 100 and sal_text.lower() != 'not disclosed':
                    salary = sal_text
                    break
        
        # If salary not in selector, search page text
        if salary == "Not disclosed":
            salary_patterns = [
                r'₹\s*(\d+(?:,\d+)*)\s*-\s*₹?\s*(\d+(?:,\d+)*)',
                r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:lacs?|lakhs?)\s*p\.?a\.?',
                r'(\d+(?:\.\d+)?)\s*lpa',
            ]
            
            for pattern in salary_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    if match.group(2) if len(match.groups()) > 1 else False:
                        num1 = match.group(1).replace(',', '')
                        num2 = match.group(2).replace(',', '')
                        if 'lac' in page_text or 'lakh' in page_text:
                            salary = f"₹{num1}-{num2} Lacs P.A."
                        else:
                            salary = f"₹{num1}-{num2}"
                    else:
                        num = match.group(1).replace(',', '')
                        if 'lpa' in page_text:
                            salary = f"{num} LPA"
                    break
        
        # Filter by salary if specified
        if min_salary and salary != "Not disclosed":
            salary_nums = re.findall(r'(\d+(?:,\d+)*)', salary)
            if salary_nums:
                job_salary = int(salary_nums[0].replace(',', ''))
                if 'lpa' in salary.lower() or 'lakh' in salary.lower():
                    job_salary = job_salary * 100000
                elif job_salary < 100000:
                    job_salary = job_salary * 1000
                
                if job_salary < min_salary:
                    print(f"  ⏭️  Salary too low: {salary}")
                    return None
        
        # Extract EXPERIENCE
        experience = "Not disclosed"
        exp_patterns = [
            r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)',
            r'fresher',
            r'0\s*(?:years?|yrs?)',
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                if 'fresher' in pattern:
                    experience = "Fresher"
                elif len(match.groups()) > 1 and match.group(2):
                    experience = f"{match.group(1)}-{match.group(2)} years"
                else:
                    exp_num = match.group(1)
                    if exp_num == '0':
                        experience = "Fresher"
                    else:
                        experience = f"{exp_num}+ years"
                break
        
        if experience == "Not disclosed":
            experience = "Check job details"
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "experience": experience,
            "link": url,
            "source": "Naukri"
        }
        
    except Exception as e:
        print(f"  ⚠️ Job page scraping error: {e}")
        return None
