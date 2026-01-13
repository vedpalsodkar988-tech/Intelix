from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import re
import sqlite3
from datetime import datetime, timedelta

def check_daily_limit(user_id):
    """
    Check if user has exceeded 3 searches per day (FREE tier)
    Returns: (allowed: bool, searches_today: int)
    """
    try:
        conn = sqlite3.connect('agent_system.db')
        c = conn.cursor()
        
        # Create job searches table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS job_searches
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      search_date DATE,
                      FOREIGN KEY(user_id) REFERENCES users(id))''')
        
        # Count searches today
        today = datetime.now().date()
        c.execute('SELECT COUNT(*) FROM job_searches WHERE user_id = ? AND search_date = ?',
                  (user_id, today))
        count = c.fetchone()[0]
        
        conn.close()
        
        # FREE tier: 3 searches per day
        FREE_LIMIT = 3
        return (count < FREE_LIMIT, count)
        
    except Exception as e:
        print(f"Error checking limit: {e}")
        return (True, 0)  # Allow on error


def record_search(user_id):
    """Record that user performed a job search today"""
    try:
        conn = sqlite3.connect('agent_system.db')
        c = conn.cursor()
        today = datetime.now().date()
        c.execute('INSERT INTO job_searches (user_id, search_date) VALUES (?, ?)',
                  (user_id, today))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error recording search: {e}")


def filter_top_jobs(jobs, top_n=3):
    """
    Filter top jobs based on:
    1. Salary (if available)
    2. Company quality (Fortune companies, well-known brands)
    3. Job relevance
    """
    # Known good companies (add more as needed)
    top_companies = ['google', 'microsoft', 'amazon', 'facebook', 'meta', 'apple', 
                     'netflix', 'uber', 'airbnb', 'linkedin', 'twitter', 'adobe',
                     'salesforce', 'oracle', 'ibm', 'intel', 'nvidia', 'cisco',
                     'infosys', 'tcs', 'wipro', 'hcl', 'tech mahindra', 'cognizant',
                     'accenture', 'deloitte', 'pwc', 'ey', 'kpmg', 'flipkart',
                     'paytm', 'zomato', 'swiggy', 'ola', 'byju', 'razorpay']
    
    def calculate_score(job):
        """Calculate job score based on multiple factors"""
        score = 0
        
        # Salary score (higher is better)
        salary_text = job.get('salary', '').lower()
        if salary_text and salary_text != 'not disclosed':
            # Extract numbers from salary
            numbers = re.findall(r'\d+', salary_text.replace(',', ''))
            if numbers:
                # Get the highest number (likely the max salary)
                max_salary = max([int(n) for n in numbers])
                
                # Score based on salary ranges (Indian market)
                if max_salary >= 2000000:  # 20+ LPA
                    score += 100
                elif max_salary >= 1500000:  # 15+ LPA
                    score += 80
                elif max_salary >= 1000000:  # 10+ LPA
                    score += 60
                elif max_salary >= 500000:  # 5+ LPA
                    score += 40
                else:
                    score += 20
        
        # Company score (top companies get bonus)
        company = job.get('company', '').lower()
        for top_company in top_companies:
            if top_company in company:
                score += 50
                break
        
        # Title relevance (senior positions get bonus)
        title = job.get('title', '').lower()
        if any(word in title for word in ['senior', 'lead', 'principal', 'architect', 'manager']):
            score += 30
        elif any(word in title for word in ['mid', 'intermediate']):
            score += 15
        
        return score
    
    # Score all jobs
    for job in jobs:
        job['_score'] = calculate_score(job)
    
    # Sort by score (highest first)
    sorted_jobs = sorted(jobs, key=lambda x: x['_score'], reverse=True)
    
    # Remove the internal score before returning
    top_jobs = sorted_jobs[:top_n]
    for job in top_jobs:
        if '_score' in job:
            del job['_score']
    
    return top_jobs


def extract_job_details_from_query(query):
    """
    Extract job title, location from natural language query
    Examples:
    - "find python developer jobs in bangalore"
    - "search for marketing jobs"
    - "get software engineer positions in remote"
    """
    query_lower = query.lower()
    
    # Extract location
    location_patterns = [
        r'in\s+([\w\s]+?)(?:\s|$)',  # "in bangalore"
        r'at\s+([\w\s]+?)(?:\s|$)',  # "at bangalore"
        r'location\s+([\w\s]+?)(?:\s|$)',
    ]
    
    location = None
    for pattern in location_patterns:
        match = re.search(pattern, query_lower)
        if match:
            location = match.group(1).strip()
            break
    
    # Extract job title
    # Remove command words and location
    job_title = query_lower
    remove_words = ['find', 'search', 'get', 'looking for', 'jobs', 'job', 'positions', 'position', 'in', 'at', 'for']
    for word in remove_words:
        job_title = job_title.replace(word, ' ')
    
    if location:
        job_title = job_title.replace(location, '')
    
    job_title = ' '.join(job_title.split()).strip()
    
    return job_title, location


def jobsearch_task(query, user_profile=None):
    """
    AI Job Finder - Searches Indeed for matching jobs
    FREE Version: 3 searches per day
    """
    print("💼 AI Job Finder Starting...")
    print(f"Query: {query}")
    
    result = {
        "status": "error",
        "jobs": [],
        "message": "",
        "searches_used": 0,
        "searches_remaining": 3
    }
    
    # Check if user_profile has user_id for limit checking
    user_id = None
    if user_profile and len(user_profile) > 0:
        user_id = user_profile[1]  # user_id is typically second column
    
    # Check daily limit (FREE tier: 3 searches/day)
    if user_id:
        allowed, searches_today = check_daily_limit(user_id)
        result["searches_used"] = searches_today
        result["searches_remaining"] = max(0, 3 - searches_today)
        
        if not allowed:
            result["message"] = f"❌ Daily limit reached! You've used all 3 FREE searches today. Upgrade to Premium for unlimited searches!"
            return result
    
    # Extract job details from query
    job_title, location = extract_job_details_from_query(query)
    
    # Use profile data if available and query doesn't specify
    if user_profile:
        try:
            profile_job_title = user_profile[14] if len(user_profile) > 14 else None  # preferred_job_title
            profile_location = user_profile[15] if len(user_profile) > 15 else None  # preferred_location
            
            if not job_title or len(job_title) < 3:
                job_title = profile_job_title
            
            if not location:
                location = profile_location
                
        except Exception as e:
            print(f"Could not read profile: {e}")
    
    if not job_title or len(job_title) < 2:
        result["message"] = "❌ Please specify a job title. Example: 'find python developer jobs'"
        return result
    
    if not location:
        location = "India"  # Default location
    
    print(f"✓ Job Title: {job_title}")
    print(f"✓ Location: {location}")
    
    # Record this search
    if user_id:
        record_search(user_id)
        result["searches_used"] += 1
        result["searches_remaining"] -= 1
    
    # Search Indeed using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        
        try:
            # Build Indeed search URL
            job_query = job_title.replace(' ', '+')
            location_query = location.replace(' ', '+')
            indeed_url = f"https://in.indeed.com/jobs?q={job_query}&l={location_query}"
            
            print(f"🔍 Opening Indeed: {indeed_url}")
            page.goto(indeed_url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(3000)
            
            # Extract job listings
            print("📋 Extracting job listings...")
            
            # Wait for job cards to load
            try:
                page.wait_for_selector('.job_seen_beacon, .resultContent', timeout=10000)
            except:
                print("⚠️ Job cards taking time to load...")
            
            page.wait_for_timeout(2000)
            
            # Get all job cards
            job_cards = page.locator('.job_seen_beacon, .resultContent').all()[:10]  # Get top 10
            
            print(f"Found {len(job_cards)} job listings")
            
            jobs_found = []
            
            for idx, card in enumerate(job_cards):
                try:
                    # Extract job title
                    try:
                        title_elem = card.locator('h2 a span, .jobTitle span').first
                        job_title_text = title_elem.inner_text(timeout=2000)
                    except:
                        continue
                    
                    # Extract company name
                    try:
                        company_elem = card.locator('[data-testid="company-name"], .companyName').first
                        company = company_elem.inner_text(timeout=2000)
                    except:
                        company = "Company not listed"
                    
                    # Extract location
                    try:
                        location_elem = card.locator('[data-testid="text-location"], .companyLocation').first
                        job_location = location_elem.inner_text(timeout=2000)
                    except:
                        job_location = location
                    
                    # Extract salary if available
                    try:
                        salary_elem = card.locator('.salary-snippet, .salaryOnly').first
                        salary = salary_elem.inner_text(timeout=2000)
                    except:
                        salary = "Not disclosed"
                    
                    # Extract job link
                    try:
                        link_elem = card.locator('h2 a').first
                        job_link = link_elem.get_attribute('href', timeout=2000)
                        if job_link and not job_link.startswith('http'):
                            job_link = 'https://in.indeed.com' + job_link
                    except:
                        job_link = indeed_url
                    
                    # Extract job snippet/description
                    try:
                        snippet_elem = card.locator('.job-snippet, .underShelfFooter').first
                        snippet = snippet_elem.inner_text(timeout=2000)[:200]  # First 200 chars
                    except:
                        snippet = "No description available"
                    
                    job_data = {
                        "title": job_title_text,
                        "company": company,
                        "location": job_location,
                        "salary": salary,
                        "snippet": snippet,
                        "link": job_link
                    }
                    
                    jobs_found.append(job_data)
                    print(f"✓ Job {idx+1}: {job_title_text} at {company}")
                    
                except Exception as e:
                    print(f"✗ Skipping job {idx+1}: {e}")
                    continue
            
            if jobs_found:
                # FREE VERSION: Filter TOP 3 jobs (best salary + best companies)
                top_jobs = filter_top_jobs(jobs_found, top_n=3)
                
                result["status"] = "success"
                result["jobs"] = top_jobs
                result["total_found"] = len(jobs_found)
                result["message"] = f"✅ Found {len(jobs_found)} jobs. Showing TOP 3 best matches!"
                print(f"\n✅ Successfully found {len(jobs_found)} jobs! Filtered to TOP 3")
            else:
                result["status"] = "error"
                result["message"] = f"❌ No jobs found for '{job_title}' in {location}. Try different keywords."
            
            # Keep browser open so user can see and apply manually
            print("\n👀 Browser will stay open. You can view and apply to jobs!")
            print("   Close the browser window when done.")
            page.wait_for_timeout(120000)  # 2 minutes
            
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"❌ Error searching jobs: {str(e)}"
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()
    
    return result


# Test function
if __name__ == "__main__":
    test_query = "find python developer jobs in bangalore"
    result = jobsearch_task(test_query)
    print("\n" + "="*60)
    print("RESULT:")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Jobs found: {len(result['jobs'])}")
    if result['jobs']:
        for idx, job in enumerate(result['jobs'][:3], 1):
            print(f"\n{idx}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")