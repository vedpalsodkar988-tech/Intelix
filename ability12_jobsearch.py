import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


def scrape_with_scraperapi(url, api_key):
    """Use ScraperAPI to bypass anti-bot protection"""
    try:
        scraperapi_url = 'http://api.scraperapi.com'
        
        params = {
            'api_key': api_key,
            'url': url,
            'country_code': 'in'
        }
        
        response = requests.get(scraperapi_url, params=params, timeout=60)
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"    ❌ ScraperAPI returned status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"    ❌ ScraperAPI error: {e}")
        return None


def scrape_naukri_jobs(query, location, scraperapi_key):
    """Scrape Naukri.com for jobs"""
    print("  💼 Scraping Naukri.com...")
    
    try:
        # Naukri search URL
        search_url = f"https://www.naukri.com/{quote_plus(query)}-jobs-in-{quote_plus(location)}"
        
        print(f"    📡 Using ScraperAPI to fetch Naukri...")
        html_content = scrape_with_scraperapi(search_url, scraperapi_key)
        
        if not html_content:
            print(f"  ❌ Failed to get Naukri page")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []
        
        # Find job cards - Naukri uses article tags with specific class
        job_cards = soup.find_all('article', class_='jobTuple')
        if not job_cards:
            job_cards = soup.find_all('div', class_='jobTuple')
        
        print(f"  ✅ Found {len(job_cards)} Naukri jobs")
        
        for card in job_cards[:5]:
            try:
                # Get job title
                title_elem = card.find('a', class_='title') or card.find('a', class_='jobTitle')
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                if not title or len(title) < 5:
                    continue
                
                # Get company name
                company_elem = card.find('a', class_='subTitle') or card.find('div', class_='companyInfo')
                company = company_elem.get_text().strip() if company_elem else "Company Not Listed"
                
                # Get location
                loc_elem = card.find('li', class_='location') or card.find('span', class_='locWdth')
                job_location = loc_elem.get_text().strip() if loc_elem else location
                
                # Get salary
                salary_elem = card.find('li', class_='salary') or card.find('span', class_='salary')
                salary = salary_elem.get_text().strip() if salary_elem else "Not Disclosed"
                
                # Get experience
                exp_elem = card.find('li', class_='experience') or card.find('span', class_='expwdth')
                experience = exp_elem.get_text().strip() if exp_elem else "Not Specified"
                
                # Get job link
                link = title_elem.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://www.naukri.com{link}"
                
                if not link:
                    continue
                
                # Get job snippet/description
                snippet_elem = card.find('div', class_='jobDescription') or card.find('ul', class_='list')
                snippet = snippet_elem.get_text().strip()[:200] if snippet_elem else "No description available"
                
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "salary": salary,
                    "experience": experience,
                    "snippet": snippet,
                    "link": link,
                    "source": "Naukri.com"
                })
                
                print(f"    ✓ Naukri: {title[:40]}... at {company}")
                
            except Exception as e:
                print(f"    ✗ Error parsing Naukri job: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"  ❌ Naukri scraping error: {e}")
        import traceback
        traceback.print_exc()
        return []


def scrape_indeed_jobs(query, location, scraperapi_key):
    """Scrape Indeed India for jobs"""
    print("  💼 Scraping Indeed India...")
    
    try:
        # Indeed search URL
        search_url = f"https://in.indeed.com/jobs?q={quote_plus(query)}&l={quote_plus(location)}"
        
        print(f"    📡 Using ScraperAPI to fetch Indeed...")
        html_content = scrape_with_scraperapi(search_url, scraperapi_key)
        
        if not html_content:
            print(f"  ❌ Failed to get Indeed page")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []
        
        # Find job cards - Indeed uses div with data-jk attribute
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        if not job_cards:
            job_cards = soup.find_all('td', class_='resultContent')
        
        print(f"  ✅ Found {len(job_cards)} Indeed jobs")
        
        for card in job_cards[:5]:
            try:
                # Get job title
                title_elem = card.find('h2', class_='jobTitle') or card.find('a', class_='jcs-JobTitle')
                if not title_elem:
                    # Try finding any h2 or span with job title
                    title_elem = card.find('h2') or card.find('span', {'title': True})
                
                if not title_elem:
                    continue
                
                # Extract title text
                title_link = title_elem.find('a') if title_elem.find('a') else title_elem
                title = title_link.get_text().strip()
                
                if not title or len(title) < 5:
                    continue
                
                # Get company name
                company_elem = card.find('span', class_='companyName') or card.find('span', {'data-testid': 'company-name'})
                company = company_elem.get_text().strip() if company_elem else "Company Not Listed"
                
                # Get location
                loc_elem = card.find('div', class_='companyLocation')
                job_location = loc_elem.get_text().strip() if loc_elem else location
                
                # Get salary
                salary_elem = card.find('div', class_='salary-snippet')
                salary = salary_elem.get_text().strip() if salary_elem else "Not Disclosed"
                
                # Get job link
                link_elem = card.find('a', href=True)
                link = link_elem.get('href', '') if link_elem else ''
                
                if link and not link.startswith('http'):
                    link = f"https://in.indeed.com{link}"
                
                if not link:
                    continue
                
                # Get job snippet
                snippet_elem = card.find('div', class_='job-snippet') or card.find('ul')
                snippet = snippet_elem.get_text().strip()[:200] if snippet_elem else "No description available"
                
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "salary": salary,
                    "snippet": snippet,
                    "link": link,
                    "source": "Indeed India"
                })
                
                print(f"    ✓ Indeed: {title[:40]}... at {company}")
                
            except Exception as e:
                print(f"    ✗ Error parsing Indeed job: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"  ❌ Indeed scraping error: {e}")
        import traceback
        traceback.print_exc()
        return []


def jobsearch_task(query, user_profile=None):
    """AI Job Search Assistant using ScraperAPI"""
    print("💼 AI Job Search Starting (ScraperAPI)...")
    print(f"Query: {query}")
    
    # Extract job title and location from query
    query_lower = query.lower()
    
    # Try to extract location from query
    location = "India"
    location_keywords = ['in ', ' at ', ' from ']
    for keyword in location_keywords:
        if keyword in query_lower:
            parts = query_lower.split(keyword)
            if len(parts) > 1:
                location = parts[-1].strip()
                query = parts[0].strip()
                break
    
    # If user has profile, use their preferred location
    if user_profile and user_profile.get('preferred_location'):
        location = user_profile['preferred_location']
    
    # Clean the job title query
    job_title = re.sub(r'\b(find|search|job|jobs|for|looking|need)\b', '', query.lower()).strip()
    job_title = re.sub(r'\s+', ' ', job_title)
    
    # If user has profile, use their preferred job title if query is generic
    if user_profile and user_profile.get('preferred_job_title') and len(job_title) < 3:
        job_title = user_profile['preferred_job_title']
    
    print(f"Searching for: '{job_title}' in '{location}'")
    
    # Get ScraperAPI key
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    if not scraperapi_key:
        print("❌ ERROR: SCRAPERAPI_KEY not found in environment variables!")
        return {"status": "error", "message": "ScraperAPI key not configured"}
    
    print(f"✅ ScraperAPI Key loaded")
    
    try:
        all_jobs = []
        
        # Scrape Naukri
        naukri_jobs = scrape_naukri_jobs(job_title, location, scraperapi_key)
        all_jobs.extend(naukri_jobs)
        
        # Scrape Indeed
        indeed_jobs = scrape_indeed_jobs(job_title, location, scraperapi_key)
        all_jobs.extend(indeed_jobs)
        
        if not all_jobs:
            print("⚠️ No jobs found on Naukri or Indeed")
            return {
                "status": "error", 
                "message": f"No jobs found for '{job_title}' in '{location}'. Try different keywords.",
                "suggestion": "Try broader terms like 'software developer', 'data analyst', 'marketing'"
            }
        
        # Sort by relevance (jobs with salary info first)
        all_jobs.sort(key=lambda x: 0 if x['salary'] != 'Not Disclosed' else 1)
        
        print(f"\n✅ Found {len(all_jobs)} total jobs")
        print(f"🎯 TOP JOB: {all_jobs[0]['title'][:50]}... at {all_jobs[0]['company']}")
        
        return {
            "status": "success",
            "jobs": all_jobs[:5],  # Return top 5 jobs
            "total_found": len(all_jobs),
            "query": job_title,
            "location": location,
            "message": f"🎉 Found {len(all_jobs)} jobs for '{job_title}' in '{location}'!"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}
