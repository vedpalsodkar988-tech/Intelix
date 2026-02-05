import os
import re
import requests
from bs4 import BeautifulSoup

def jobsearch_task(query, user_profile=None):
    """
    AI Job Search Agent - Searches multiple job boards
    FIXED: Now properly extracts job role from query
    """
    print(f"💼 AI Job Search Starting...")
    print(f"Original query: {query}")
    
    # CRITICAL FIX: Extract the actual role from the query
    # Remove common words like "find", "search", "job", "jobs", etc.
    clean_query = query.lower()
    
    # Remove these words
    remove_words = [
        'find', 'search', 'get', 'show', 'looking for', 'look for',
        'job', 'jobs', 'position', 'positions', 'for', 'in', 'at',
        'give me', 'get me', 'i want', 'i need', 'opening', 'openings'
    ]
    
    for word in remove_words:
        clean_query = re.sub(r'\b' + word + r'\b', '', clean_query, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    # If query is now empty, use profile or default
    if not clean_query:
        if user_profile and user_profile.get('preferred_job_title'):
            clean_query = user_profile['preferred_job_title']
        else:
            clean_query = "software engineer"
    
    print(f"✅ Cleaned query for job boards: '{clean_query}'")
    
    # Get ScraperAPI key
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    if not scraperapi_key:
        return {"status": "error", "message": "ScraperAPI key not configured"}
    
    try:
        all_jobs = []
        
        # Search Naukri.com
        print("🔍 Searching Naukri.com...")
        naukri_jobs = scrape_naukri(clean_query, scraperapi_key)
        all_jobs.extend(naukri_jobs)
        
        # Search Indeed
        print("🔍 Searching Indeed...")
        indeed_jobs = scrape_indeed(clean_query, scraperapi_key)
        all_jobs.extend(indeed_jobs)
        
        if not all_jobs:
            return {
                "status": "error",
                "message": f"No jobs found for '{clean_query}'. Try different keywords."
            }
        
        # Sort by relevance (if salary available, prefer those)
        all_jobs.sort(key=lambda x: 1 if x.get('salary') else 0, reverse=True)
        
        # Return TOP 5
        top_jobs = all_jobs[:5]
        
        print(f"🎉 Found {len(all_jobs)} total jobs, returning TOP 5!")
        
        return {
            "status": "success",
            "jobs": top_jobs,
            "total_found": len(all_jobs),
            "query": clean_query,
            "message": f"💼 Found {len(top_jobs)} jobs for '{clean_query}'! Showing TOP 5:"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to search jobs: {str(e)}"
        }


def scrape_naukri(query, api_key):
    """Scrape Naukri.com"""
    jobs = []
    try:
        # Build Naukri URL
        search_term = query.replace(' ', '-')
        naukri_url = f"https://www.naukri.com/{search_term}-jobs"
        
        api_url = f"http://api.scraperapi.com?api_key={api_key}&url={naukri_url}"
        response = requests.get(api_url, timeout=60)
        
        if response.status_code != 200:
            print(f"⚠️ Naukri returned status: {response.status_code}")
            return jobs
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job cards
        job_cards = soup.find_all('article', class_='jobTuple')
        
        for card in job_cards[:3]:  # TOP 3 from Naukri
            try:
                title_elem = card.find('a', class_='title')
                title = title_elem.get_text(strip=True) if title_elem else "Job"
                
                company_elem = card.find('a', class_='subTitle')
                company = company_elem.get_text(strip=True) if company_elem else "Company"
                
                exp_elem = card.find('li', class_='experience')
                experience = exp_elem.get_text(strip=True) if exp_elem else "N/A"
                
                salary_elem = card.find('li', class_='salary')
                salary = salary_elem.get_text(strip=True) if salary_elem else None
                
                location_elem = card.find('li', class_='location')
                location = location_elem.get_text(strip=True) if location_elem else "India"
                
                link_elem = card.find('a', class_='title')
                link = "https://www.naukri.com" + link_elem['href'] if link_elem and link_elem.get('href') else None
                
                job = {
                    "title": title,
                    "company": company,
                    "experience": experience,
                    "salary": salary,
                    "location": location,
                    "link": link,
                    "source": "Naukri"
                }
                
                jobs.append(job)
                print(f"✅ Naukri: {title} at {company}")
                
            except Exception as e:
                print(f"⚠️ Error parsing Naukri job: {e}")
                continue
                
    except Exception as e:
        print(f"⚠️ Naukri scraping failed: {e}")
    
    return jobs


def scrape_indeed(query, api_key):
    """Scrape Indeed.co.in"""
    jobs = []
    try:
        # Build Indeed URL
        search_term = query.replace(' ', '+')
        indeed_url = f"https://in.indeed.com/jobs?q={search_term}&l=India"
        
        api_url = f"http://api.scraperapi.com?api_key={api_key}&url={indeed_url}"
        response = requests.get(api_url, timeout=60)
        
        if response.status_code != 200:
            print(f"⚠️ Indeed returned status: {response.status_code}")
            return jobs
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job cards
        job_cards = soup.find_all('div', class_='job_seen_beacon') or soup.find_all('td', class_='resultContent')
        
        for card in job_cards[:2]:  # TOP 2 from Indeed
            try:
                title_elem = card.find('h2', class_='jobTitle') or card.find('a')
                title = title_elem.get_text(strip=True) if title_elem else "Job"
                
                company_elem = card.find('span', class_='companyName')
                company = company_elem.get_text(strip=True) if company_elem else "Company"
                
                location_elem = card.find('div', class_='companyLocation')
                location = location_elem.get_text(strip=True) if location_elem else "India"
                
                salary_elem = card.find('div', class_='salary-snippet')
                salary = salary_elem.get_text(strip=True) if salary_elem else None
                
                link_elem = card.find('a', class_='jcs-JobTitle')
                link = "https://in.indeed.com" + link_elem['href'] if link_elem and link_elem.get('href') else None
                
                job = {
                    "title": title,
                    "company": company,
                    "experience": "As per requirement",
                    "salary": salary,
                    "location": location,
                    "link": link,
                    "source": "Indeed"
                }
                
                jobs.append(job)
                print(f"✅ Indeed: {title} at {company}")
                
            except Exception as e:
                print(f"⚠️ Error parsing Indeed job: {e}")
                continue
                
    except Exception as e:
        print(f"⚠️ Indeed scraping failed: {e}")
    
    return jobs
