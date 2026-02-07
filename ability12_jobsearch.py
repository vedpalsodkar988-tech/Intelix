import os
import re
import requests

def jobsearch_task(query, user_profile=None):
    """
    AI Job Search - GENIUS METHOD!
    Uses Google: "python developer" site:naukri.com
    Gets REAL job URLs from Naukri/LinkedIn/Indeed!
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
    
    print(f"✅ Query: '{clean_query}'" + (f" in {location}" if location else ""))
    
    # Get SerpAPI key
    serpapi_key = os.environ.get('SERPAPI_KEY', '').strip()
    
    if not serpapi_key:
        return {"status": "error", "message": "Search service not configured"}
    
    try:
        all_jobs = []
        
        # Search Naukri via Google
        print("🔍 Searching Naukri via Google...")
        naukri_jobs = search_via_google(clean_query, location, "naukri.com/job-listings", serpapi_key)
        all_jobs.extend(naukri_jobs)
        
        # Search LinkedIn via Google
        print("🔍 Searching LinkedIn via Google...")
        linkedin_jobs = search_via_google(clean_query, location, "linkedin.com/jobs/view", serpapi_key)
        all_jobs.extend(linkedin_jobs)
        
        # Search Indeed via Google  
        print("🔍 Searching Indeed via Google...")
        indeed_jobs = search_via_google(clean_query, location, "in.indeed.com/viewjob", serpapi_key)
        all_jobs.extend(indeed_jobs)
        
        if not all_jobs:
            return {
                "status": "error",
                "message": f"No jobs found for '{clean_query}'. Try: 'software engineer', 'data analyst', 'marketing manager'."
            }
        
        # Remove duplicates
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job['link'] not in seen:
                seen.add(job['link'])
                unique_jobs.append(job)
        
        print(f"🎉 Found {len(unique_jobs)} unique jobs!")
        
        return {
            "status": "success",
            "jobs": unique_jobs[:5],
            "total_found": len(unique_jobs),
            "query": clean_query,
            "message": f"💼 Found {len(unique_jobs[:5])} jobs for '{clean_query}'!"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": "Job search failed. Please try again."
        }


def search_via_google(query, location, site, api_key):
    """
    GENIUS: Google search with site: operator
    Example: "python developer pune" site:naukri.com
    Returns REAL Naukri job URLs!
    """
    jobs = []
    
    try:
        # Build Google query
        google_query = f'"{query}"'
        if location:
            google_query += f' {location}'
        google_query += f' site:{site}'
        
        print(f"📡 Query: {google_query}")
        
        # SerpAPI
        url = "https://serpapi.com/search"
        params = {
            'engine': 'google',
            'q': google_query,
            'api_key': api_key,
            'num': 10,
            'hl': 'en',
            'gl': 'in'
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"⚠️ Status: {response.status_code}")
            return jobs
        
        data = response.json()
        
        if 'error' in data:
            print(f"⚠️ Error: {data['error']}")
            return jobs
        
        # Get results
        results = data.get('organic_results', [])
        print(f"📋 Found {len(results)} results")
        
        for result in results:
            try:
                title = result.get('title', '')
                link = result.get('link', '')
                snippet = result.get('snippet', '')
                
                if not link or site not in link:
                    continue
                
                # SMART PARSING with city detection
                INDIAN_CITIES = ['pune', 'mumbai', 'bangalore', 'bengaluru', 'delhi', 'ncr', 
                                'hyderabad', 'chennai', 'kolkata', 'ahmedabad', 'gurgaon', 
                                'noida', 'kochi', 'jaipur', 'chandigarh', 'indore', 'remote']
                
                company = "Company"
                job_location = location or "India"
                job_title = title
                
                if ' - ' in title:
                    parts = [p.strip() for p in title.split(' - ')]
                    job_title = parts[0]  # First part is always job title
                    
                    # Identify cities vs companies
                    for part in parts[1:]:
                        part_lower = part.lower()
                        # Check if it's a city
                        if any(city in part_lower for city in INDIAN_CITIES):
                            job_location = part
                        # Otherwise it's a company
                        elif company == "Company":
                            company = part
                
                # Source
                if 'naukri.com' in link:
                    source = "Naukri"
                elif 'linkedin.com' in link:
                    source = "LinkedIn"
                elif 'indeed' in link:
                    source = "Indeed"
                else:
                    source = "Job Board"
                
                job = {
                    "title": job_title,
                    "company": company,
                    "location": job_location,
                    "salary": "Not disclosed",
                    "experience": "Check job details",
                    "link": link,
                    "source": source
                }
                
                jobs.append(job)
                print(f"✅ {job_title} at {company} ({source})")
                
            except Exception as e:
                print(f"⚠️ Parse error: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return jobs
