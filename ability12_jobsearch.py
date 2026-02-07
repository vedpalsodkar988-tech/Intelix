import os
import re
import requests

def jobsearch_task(query, user_profile=None):
    """
    AI Job Search - WITH SALARY & LOCATION FILTERING!
    Example: "Find software engineer jobs in Pune, salary 1,00,000+"
    """
    print(f"💼 AI Job Search Starting...")
    print(f"Original query: {query}")
    
    original_query = query
    clean_query = query.lower()
    
    # STEP 1: Extract salary requirements
    min_salary = None
    salary_patterns = [
        (r'salary[:\s]+₹?\s*(\d+(?:,\d+)*)\s*\+?', 'absolute'),  # "salary: 100000" or "salary ₹1,00,000+"
        (r'₹\s*(\d+(?:,\d+)*)\s*\+?', 'absolute'),                # "₹100000+" or "₹1,00,000+"
        (r'(\d+)\s*lpa\s*\+?', 'lpa'),                            # "5 LPA+" or "10LPA+"
        (r'(\d+)\s*-\s*(\d+)\s*lpa', 'lpa_range'),               # "5-8 LPA"
    ]
    
    for pattern, salary_type in salary_patterns:
        match = re.search(pattern, clean_query, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(',', '')
            
            if salary_type == 'lpa' or salary_type == 'lpa_range':
                # Convert LPA to annual amount
                min_salary = int(num_str) * 100000
                print(f"💰 Salary filter: {num_str}+ LPA (₹{min_salary:,}+ per year)")
            else:
                min_salary = int(num_str)
                print(f"💰 Salary filter: ₹{min_salary:,}+ minimum")
            
            # Remove salary part from query
            clean_query = re.sub(pattern, '', clean_query, flags=re.IGNORECASE)
            break
    
    # STEP 2: Extract location
    location = None
    location_keywords = {
        'pune': 'Pune',
        'mumbai': 'Mumbai',
        'bangalore': 'Bangalore',
        'bengaluru': 'Bangalore',
        'delhi': 'Delhi',
        'ncr': 'Delhi NCR',
        'hyderabad': 'Hyderabad',
        'chennai': 'Chennai',
        'kolkata': 'Kolkata',
        'gurgaon': 'Gurgaon',
        'noida': 'Noida',
        'remote': 'Remote'
    }
    
    for keyword, city in location_keywords.items():
        if keyword in clean_query:
            location = city
            clean_query = clean_query.replace(keyword, '').strip()
            print(f"📍 Location filter: {location} ONLY")
            break
    
    # STEP 3: Remove common words
    remove_words = [
        'find', 'search', 'get', 'show', 'looking for', 'look for',
        'job', 'jobs', 'position', 'positions', 'for', 'in', 'at',
        'give me', 'get me', 'i want', 'i need', 'opening', 'openings',
        'salary', 'range', 'lpa', 'per', 'month', 'year', 'annual',
        'minimum', 'above', 'below', 'between'
    ]
    
    for word in remove_words:
        clean_query = re.sub(r'\b' + word + r'\b', '', clean_query, flags=re.IGNORECASE)
    
    clean_query = re.sub(r'[:\-,\+]', ' ', clean_query)  # Remove punctuation
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    if not clean_query:
        clean_query = "software engineer"
    
    print(f"✅ Final search: '{clean_query}'" + (f" in {location}" if location else ""))
    
    # Get SerpAPI key
    serpapi_key = os.environ.get('SERPAPI_KEY', '').strip()
    
    if not serpapi_key:
        return {"status": "error", "message": "Search service not configured"}
    
    try:
        all_jobs = []
        
        # Search Naukri via Google
        print("🔍 Searching Naukri...")
        naukri_jobs = search_via_google(clean_query, location, "naukri.com/job-listings", serpapi_key)
        all_jobs.extend(naukri_jobs)
        
        # Search LinkedIn via Google
        print("🔍 Searching LinkedIn...")
        linkedin_jobs = search_via_google(clean_query, location, "linkedin.com/jobs/view", serpapi_key)
        all_jobs.extend(linkedin_jobs)
        
        # Search Indeed via Google  
        print("🔍 Searching Indeed...")
        indeed_jobs = search_via_google(clean_query, location, "in.indeed.com/viewjob", serpapi_key)
        all_jobs.extend(indeed_jobs)
        
        # FILTER RESULTS
        filtered_jobs = []
        
        for job in all_jobs:
            # Location filter (if specified)
            if location:
                job_loc = job['location'].lower()
                if location.lower() not in job_loc and location.lower() not in job['title'].lower():
                    print(f"⏭️  Skipped: {job['title']} (Location: {job['location']} != {location})")
                    continue
            
            # Salary filter (if specified and salary is disclosed)
            if min_salary and job['salary'] != "Not disclosed":
                # Try to extract salary from job
                salary_str = job['salary'].lower()
                
                # Extract numbers from salary string
                salary_nums = re.findall(r'(\d+(?:,\d+)*)', salary_str)
                
                if salary_nums:
                    # Convert to int (remove commas)
                    job_salary = int(salary_nums[0].replace(',', ''))
                    
                    # If salary is in thousands or lakhs, convert
                    if 'lpa' in salary_str or 'lakh' in salary_str:
                        job_salary = job_salary * 100000
                    elif job_salary < 100000:  # Probably in thousands
                        job_salary = job_salary * 1000
                    
                    # Check if meets minimum
                    if job_salary < min_salary:
                        print(f"⏭️  Skipped: {job['title']} (Salary: ₹{job_salary:,} < ₹{min_salary:,})")
                        continue
            
            filtered_jobs.append(job)
        
        if not filtered_jobs:
            return {
                "status": "error",
                "message": f"No jobs found matching your criteria. Try broader search terms or remove salary/location filters."
            }
        
        # Remove duplicates
        seen = set()
        unique_jobs = []
        for job in filtered_jobs:
            if job['link'] not in seen:
                seen.add(job['link'])
                unique_jobs.append(job)
        
        print(f"🎉 Found {len(unique_jobs)} jobs matching all criteria!")
        
        return {
            "status": "success",
            "jobs": unique_jobs[:5],
            "total_found": len(unique_jobs),
            "query": clean_query,
            "filters": {
                "location": location,
                "min_salary": f"₹{min_salary:,}" if min_salary else None
            },
            "message": f"💼 Found {len(unique_jobs[:5])} jobs for '{clean_query}'" + 
                      (f" in {location}" if location else "") + 
                      (f" with salary ₹{min_salary:,}+" if min_salary else "") + "!"
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
    Search jobs using Google with strict location matching
    """
    jobs = []
    
    try:
        # Build Google query with LOCATION in query for better results
        google_query = f'"{query}"'
        
        if location:
            google_query += f' "{location}"'  # Force location in results!
        
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
        
        # Indian cities for smart parsing
        INDIAN_CITIES = ['pune', 'mumbai', 'bangalore', 'bengaluru', 'delhi', 'ncr', 
                        'hyderabad', 'chennai', 'kolkata', 'ahmedabad', 'gurgaon', 
                        'noida', 'kochi', 'jaipur', 'chandigarh', 'indore', 'remote']
        
        for result in results:
            try:
                title = result.get('title', '')
                link = result.get('link', '')
                snippet = result.get('snippet', '')
                
                if not link or site not in link:
                    continue
                
                # SMART PARSING
                company = "Company"
                job_location = location or "India"
                job_title = title
                
                if ' - ' in title:
                    parts = [p.strip() for p in title.split(' - ')]
                    job_title = parts[0]
                    
                    # Identify cities vs companies
                    for part in parts[1:]:
                        part_lower = part.lower()
                        if any(city in part_lower for city in INDIAN_CITIES):
                            job_location = part
                        elif company == "Company":
                            company = part
                
                # EXTRACT SALARY from snippet or title
                salary = "Not disclosed"
                salary_patterns = [
                    r'₹\s*(\d+(?:,\d+)*)\s*-\s*₹?\s*(\d+(?:,\d+)*)',  # ₹3,50,000 - ₹4,00,000
                    r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:lacs?|lakhs?)\s*p\.?a\.?',  # 3.5-4 Lacs P.A.
                    r'(\d+(?:\.\d+)?)\s*lpa',  # 5 LPA
                    r'₹\s*(\d+(?:,\d+)*)\s*(?:per month|pm|/month)',  # ₹50,000 per month
                ]
                
                search_text = f"{title} {snippet}".lower()
                
                for pattern in salary_patterns:
                    match = re.search(pattern, search_text, re.IGNORECASE)
                    if match:
                        if '-' in pattern and match.group(2):  # Range
                            num1 = match.group(1).replace(',', '').replace('.', '')
                            num2 = match.group(2).replace(',', '').replace('.', '')
                            
                            if 'lac' in search_text or 'lakh' in search_text:
                                salary = f"₹{num1}-{num2} Lacs P.A."
                            else:
                                salary = f"₹{num1}-{num2}"
                        else:  # Single value
                            num = match.group(1).replace(',', '').replace('.', '')
                            if 'lpa' in search_text:
                                salary = f"{num} LPA"
                            elif 'month' in search_text or 'pm' in search_text:
                                salary = f"₹{num}/month"
                            else:
                                salary = f"₹{num}"
                        break
                
                # EXTRACT EXPERIENCE from snippet or title
                experience = "Not disclosed"
                exp_patterns = [
                    r'(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)',  # 2-5 years
                    r'(\d+)\+?\s*(?:years?|yrs?)',  # 3+ years
                    r'fresher',  # Fresher
                    r'0\s*-\s*(\d+)\s*(?:years?|yrs?)',  # 0-2 years
                ]
                
                for pattern in exp_patterns:
                    match = re.search(pattern, search_text, re.IGNORECASE)
                    if match:
                        if 'fresher' in pattern:
                            experience = "Fresher"
                        elif match.group(2) if 'group(2)' in str(match.groups()) else False:
                            experience = f"{match.group(1)}-{match.group(2)} years"
                        else:
                            experience = f"{match.group(1)}+ years"
                        break
                
                # If still not found, use generic text
                if experience == "Not disclosed":
                    experience = "Check job details"
                
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
                    "salary": salary,
                    "experience": experience,
                    "link": link,
                    "source": source
                }
                
                jobs.append(job)
                print(f"✅ {job_title} at {company} | Salary: {salary} | Exp: {experience}")
                
            except Exception as e:
                print(f"⚠️ Parse error: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return jobs
