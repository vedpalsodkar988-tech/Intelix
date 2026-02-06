import os
import re
import requests
from bs4 import BeautifulSoup
import json

def jobsearch_task(query, user_profile=None):
    """
    AI Job Search - Uses Google Jobs Search
    FAST & RELIABLE: Aggregates from all job boards!
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
    
    # Clean up extra spaces
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    # Extract location if present
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
        'gurgaon': 'Gurgaon, India',
        'noida': 'Noida, India',
        'remote': 'Remote, India'
    }
    
    for keyword, city in location_keywords.items():
        if keyword in clean_query:
            location = city
            clean_query = clean_query.replace(keyword, '').strip()
            break
    
    # If query is now empty, use default
    if not clean_query:
        clean_query = "software engineer"
    
    print(f"✅ Searching Google Jobs for: '{clean_query}' in {location}")
    
    # Get ScraperAPI key
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    if not scraperapi_key:
        return {"status": "error", "message": "ScraperAPI key not configured"}
    
    try:
        jobs = search_google_jobs(clean_query, location, scraperapi_key)
        
        if not jobs:
            print("⚠️ No jobs found, trying broader search...")
            # Try with just the first word
            jobs = search_google_jobs(clean_query.split()[0], location, scraperapi_key)
        
        if not jobs:
            return {
                "status": "error",
                "message": f"No jobs found for '{clean_query}' in {location}. Try different keywords."
            }
        
        # Return TOP 5 jobs
        top_jobs = jobs[:5]
        
        print(f"🎉 Returning {len(top_jobs)} jobs!")
        
        return {
            "status": "success",
            "jobs": top_jobs,
            "total_found": len(jobs),
            "query": clean_query,
            "location": location,
            "message": f"💼 Found {len(top_jobs)} jobs for '{clean_query}' in {location}!"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Job search failed. Please try again with different keywords."
        }


def search_google_jobs(query, location, api_key):
    """
    Search jobs using Google Jobs
    Google aggregates jobs from Naukri, Indeed, LinkedIn, etc.
    """
    jobs = []
    
    try:
        # Build Google Jobs search URL
        search_query = f"{query} jobs in {location}"
        google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&ibp=htl;jobs"
        
        print(f"🔍 Google Jobs URL: {google_url}")
        
        # Use ScraperAPI
        api_url = f"http://api.scraperapi.com?api_key={api_key}&url={google_url}"
        
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            print(f"⚠️ Google Jobs returned status: {response.status_code}")
            return jobs
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Google Jobs uses specific structure
        # Look for job listing divs
        job_cards = soup.find_all('div', class_='PwjeAc')
        
        if not job_cards:
            # Try alternative selectors
            job_cards = soup.find_all('li', class_='iFjolb')
        
        if not job_cards:
            # Try finding all divs with job-related data
            job_cards = soup.find_all('div', attrs={'data-job-id': True})
        
        print(f"📋 Found {len(job_cards)} job cards")
        
        for card in job_cards[:10]:  # Process up to 10
            try:
                # Extract job title
                title_elem = (
                    card.find('div', class_='BjJfJf') or
                    card.find('h2') or
                    card.find('div', role='heading')
                )
                title = title_elem.get_text(strip=True) if title_elem else query.title()
                
                # Extract company
                company_elem = (
                    card.find('div', class_='vNEEBe') or
                    card.find('div', class_='nJlQNd')
                )
                company = company_elem.get_text(strip=True) if company_elem else "Company"
                
                # Extract location  
                location_elem = card.find('div', class_='Qk80Jf')
                job_location = location_elem.get_text(strip=True) if location_elem else location
                
                # Extract via (source)
                via_elem = card.find('div', class_='LEwnzc')
                source = via_elem.get_text(strip=True).replace('via ', '') if via_elem else "Job Board"
                
                # Try to get apply link
                link_elem = card.find('a', href=True)
                link = None
                if link_elem:
                    href = link_elem['href']
                    if href.startswith('http'):
                        link = href
                    elif href.startswith('/url?q='):
                        # Extract actual URL from Google redirect
                        link = href.split('/url?q=')[1].split('&')[0]
                
                # If no link, create a Google search link for this specific job
                if not link:
                    job_search = f"{title} {company} {job_location}".replace(' ', '+')
                    link = f"https://www.google.com/search?q={job_search}+apply"
                
                job = {
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "salary": "Not disclosed",
                    "experience": "Refer to JD",
                    "link": link,
                    "source": source
                }
                
                jobs.append(job)
                print(f"✅ {title} at {company} via {source}")
                
            except Exception as e:
                print(f"⚠️ Error parsing job card: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"❌ Google Jobs search failed: {e}")
        import traceback
        traceback.print_exc()
        return jobs
