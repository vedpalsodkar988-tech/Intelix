import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus

# Major Indian Companies & Startups Career Pages
COMPANIES = {
    'TCS': {
        'name': 'Tata Consultancy Services',
        'base_url': 'https://ibegin.tcs.com',
        'search_patterns': [
            '/iBegin/jobs/search?q={query}',
            '/iBegin/jobs/search?searchText={query}'
        ]
    },
    'Infosys': {
        'name': 'Infosys',
        'base_url': 'https://careers.infosys.com',
        'search_patterns': [
            '/jobs?q={query}',
            '/search-jobs?q={query}'
        ]
    },
    'Wipro': {
        'name': 'Wipro',
        'base_url': 'https://careers.wipro.com',
        'search_patterns': [
            '/careers-search-jobs?q={query}',
            '/job-search?keywords={query}'
        ]
    },
    'Accenture': {
        'name': 'Accenture',
        'base_url': 'https://www.accenture.com',
        'search_patterns': [
            '/in-en/careers/jobsearch?jk={query}',
            '/careers/job-search?q={query}'
        ]
    },
    'HCL Technologies': {
        'name': 'HCL Technologies',
        'base_url': 'https://www.hcltech.com',
        'search_patterns': [
            '/careers/search?q={query}',
            '/job-openings?keyword={query}'
        ]
    },
    'Tech Mahindra': {
        'name': 'Tech Mahindra',
        'base_url': 'https://careers.techmahindra.com',
        'search_patterns': [
            '/job-search?q={query}',
            '/jobs?keywords={query}'
        ]
    },
    'IBM India': {
        'name': 'IBM India',
        'base_url': 'https://www.ibm.com',
        'search_patterns': [
            '/careers/search?q={query}&country=India',
            '/in-en/careers/search?q={query}'
        ]
    },
    'Cognizant': {
        'name': 'Cognizant',
        'base_url': 'https://careers.cognizant.com',
        'search_patterns': [
            '/job-search?q={query}&location=India',
            '/jobs?keyword={query}'
        ]
    },
    'Capgemini': {
        'name': 'Capgemini India',
        'base_url': 'https://www.capgemini.com',
        'search_patterns': [
            '/in-en/careers/job-search?q={query}',
            '/careers/jobs?search={query}'
        ]
    },
    'Amazon India': {
        'name': 'Amazon',
        'base_url': 'https://www.amazon.jobs',
        'search_patterns': [
            '/en/search?base_query={query}&loc_query=India',
            '/search?q={query}&country=IND'
        ]
    },
    'Flipkart': {
        'name': 'Flipkart',
        'base_url': 'https://www.flipkartcareers.com',
        'search_patterns': [
            '/#!/joblist?q={query}',
            '/jobs?search={query}'
        ]
    },
    'Paytm': {
        'name': 'Paytm',
        'base_url': 'https://paytm.com',
        'search_patterns': [
            '/careers?q={query}',
            '/jobs?keyword={query}'
        ]
    },
    'Zomato': {
        'name': 'Zomato',
        'base_url': 'https://www.zomato.com',
        'search_patterns': [
            '/careers/jobs?q={query}',
            '/jobs?search={query}'
        ]
    },
    'Swiggy': {
        'name': 'Swiggy',
        'base_url': 'https://careers.swiggy.com',
        'search_patterns': [
            '/#/jobs?q={query}',
            '/search?keyword={query}'
        ]
    },
    'Ola': {
        'name': 'Ola',
        'base_url': 'https://www.olacabs.com',
        'search_patterns': [
            '/careers?q={query}',
            '/jobs?search={query}'
        ]
    }
}


def jobsearch_task(query, user_profile=None):
    """
    GENIUS JOB SEARCH - Scrapes company career pages directly!
    Much better than Naukri/LinkedIn!
    """
    print(f"💼 Company Career Pages Job Search Starting...")
    print(f"Original query: {query}")
    
    clean_query = query.lower()
    
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
            print(f"📍 Location filter: {location}")
            break
    
    # Clean query
    remove_words = [
        'find', 'search', 'get', 'show', 'looking for', 'look for',
        'job', 'jobs', 'position', 'positions', 'for', 'in', 'at',
        'give me', 'get me', 'i want', 'i need', 'opening', 'openings'
    ]
    
    for word in remove_words:
        clean_query = re.sub(r'\b' + word + r'\b', '', clean_query, flags=re.IGNORECASE)
    
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    if not clean_query:
        clean_query = "software engineer"
    
    print(f"✅ Searching for: '{clean_query}' on company career pages")
    
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    
    if not scraperapi_key:
        return {"status": "error", "message": "ScraperAPI not configured"}
    
    try:
        all_jobs = []
        
        # Search ONLY top 3 IT giants: TCS, Infosys, Wipro
        # These are the most trusted companies in India
        top_companies = [
            'TCS',
            'Infosys',
            'Wipro'
        ]
        
        print(f"🎯 Searching BIG 3: TCS, Infosys, Wipro")
        
        for company_key in top_companies:
            if company_key not in COMPANIES:
                continue
                
            company_data = COMPANIES[company_key]
            print(f"\n🔍 Searching {company_data['name']}...")
            
            jobs = search_company_careers(
                company_key,
                company_data,
                clean_query,
                location,
                scraperapi_key
            )
            
            all_jobs.extend(jobs)
            
            # Stop if we have enough jobs
            if len(all_jobs) >= 5:
                print(f"✅ Found enough jobs, stopping search")
                break
        
        if not all_jobs:
            return {
                "status": "error",
                "message": f"No jobs found for '{clean_query}' on company career pages. Try: 'software developer', 'data analyst', 'java developer'."
            }
        
        # Filter by location if specified
        if location:
            filtered = [j for j in all_jobs if location.lower() in j['location'].lower()]
            if filtered:
                all_jobs = filtered
        
        # Return TOP 3
        top_jobs = all_jobs[:3]
        
        print(f"\n🎉 Returning TOP {len(top_jobs)} jobs from company career pages!")
        
        return {
            "status": "success",
            "jobs": top_jobs,
            "total_found": len(all_jobs),
            "query": clean_query,
            "message": f"💼 Found {len(top_jobs)} jobs directly from company websites!"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": "Job search failed. Please try again."
        }


def search_company_careers(company_key, company_data, query, location, api_key):
    """
    Search a specific company's career page
    """
    jobs = []
    
    try:
        base_url = company_data['base_url']
        company_name = company_data['name']
        
        # Try first search pattern
        search_pattern = company_data['search_patterns'][0]
        search_url = base_url + search_pattern.format(query=quote_plus(query))
        
        print(f"  📡 URL: {search_url[:80]}...")
        
        # Use ScraperAPI
        scraper_url = f"http://api.scraperapi.com?api_key={api_key}&url={search_url}"
        response = requests.get(scraper_url, timeout=45)
        
        if response.status_code != 200:
            print(f"  ⚠️ Status {response.status_code}")
            return jobs
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Generic job card selectors (common across most career pages)
        job_cards = (
            soup.find_all('div', class_=re.compile(r'job-?card', re.I)) or
            soup.find_all('div', class_=re.compile(r'job-?item', re.I)) or
            soup.find_all('div', class_=re.compile(r'position', re.I)) or
            soup.find_all('li', class_=re.compile(r'job', re.I)) or
            soup.find_all('article', class_=re.compile(r'job', re.I))
        )
        
        print(f"  📋 Found {len(job_cards)} potential jobs")
        
        for card in job_cards[:5]:  # Max 5 jobs per company
            try:
                # Extract title
                title_elem = (
                    card.find('h2') or
                    card.find('h3') or
                    card.find('a', class_=re.compile(r'title|job-title', re.I)) or
                    card.find('span', class_=re.compile(r'title', re.I))
                )
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Skip if title doesn't match query
                if query.lower() not in title.lower():
                    continue
                
                # Extract link
                link_elem = card.find('a', href=True)
                link = None
                if link_elem:
                    href = link_elem['href']
                    link = urljoin(base_url, href)
                
                if not link:
                    link = search_url  # Fallback to search page
                
                # Extract location
                loc_elem = card.find(string=re.compile(r'Bangalore|Mumbai|Pune|Delhi|Hyderabad|Chennai|India', re.I))
                job_location = "India"
                if loc_elem:
                    job_location = loc_elem.strip()
                elif location:
                    job_location = location
                
                # Extract salary (often not on listing page)
                salary = "Not disclosed"
                sal_elem = card.find(string=re.compile(r'₹|lpa|lakh|salary', re.I))
                if sal_elem:
                    salary = sal_elem.strip()[:50]  # Max 50 chars
                
                # Extract experience
                experience = "Check job details"
                exp_elem = card.find(string=re.compile(r'\d+\s*(?:-|\+)?\s*\d*\s*(?:years?|yrs?)', re.I))
                if exp_elem:
                    exp_match = re.search(r'\d+\s*(?:-|\+)?\s*\d*\s*(?:years?|yrs?)', exp_elem, re.I)
                    if exp_match:
                        experience = exp_match.group(0)
                
                job = {
                    "title": title,
                    "company": company_name,
                    "location": job_location,
                    "salary": salary,
                    "experience": experience,
                    "link": link,
                    "source": f"{company_name} Careers"
                }
                
                jobs.append(job)
                print(f"  ✅ {title} | {job_location}")
                
            except Exception as e:
                print(f"  ⚠️ Parse error: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"  ❌ Failed for {company_name}: {e}")
        return jobs
