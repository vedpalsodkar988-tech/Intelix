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
            'country_code': 'in',
            'render': 'true'  # Important for JavaScript-heavy sites like Internshala
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


def extract_internship_query(query):
    """Extract internship role from query"""
    query_lower = query.lower()
    
    # Remove command words
    role = query_lower
    remove_words = ['find', 'search', 'get', 'looking for', 'internship', 'internships', 'for', 'in', 'need', 'want']
    for word in remove_words:
        role = role.replace(word, ' ')
    
    role = ' '.join(role.split()).strip()
    
    return role


def scrape_internshala_internships(role, location, scraperapi_key):
    """Scrape Internshala for internships"""
    print(f"  🎓 Scraping Internshala for '{role}' internships...")
    
    try:
        # Build Internshala search URL
        search_query = role.replace(' ', '-')
        
        # Add location if specified
        if location and location.lower() not in ['india', 'anywhere', 'remote']:
            location_query = location.replace(' ', '-').lower()
            search_url = f"https://internshala.com/internships/{search_query}-internship-in-{location_query}"
        else:
            search_url = f"https://internshala.com/internships/{search_query}-internship"
        
        print(f"    📡 Using ScraperAPI to fetch Internshala...")
        print(f"    🔗 URL: {search_url}")
        
        html_content = scrape_with_scraperapi(search_url, scraperapi_key)
        
        if not html_content:
            print(f"  ❌ Failed to get Internshala page")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        internships = []
        
        # Find internship cards - Internshala uses div with class 'internship_meta' or 'individual_internship'
        internship_cards = soup.find_all('div', class_='internship_meta')
        if not internship_cards:
            internship_cards = soup.find_all('div', class_='individual_internship')
        if not internship_cards:
            # Try alternative selector
            internship_cards = soup.find_all('div', attrs={'internshipid': True})
        
        print(f"  ✅ Found {len(internship_cards)} Internshala internships")
        
        for idx, card in enumerate(internship_cards[:10]):
            try:
                # Get internship title/profile
                title_elem = card.find('h3', class_='profile') or card.find('a', class_='view_detail_button')
                if not title_elem:
                    title_elem = card.find('h4') or card.find('h3')
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                if not title or len(title) < 3:
                    continue
                
                # Get company name
                company_elem = card.find('a', class_='link_display_like_text') or card.find('div', class_='company-name')
                company = company_elem.get_text().strip() if company_elem else "Company Not Listed"
                
                # Get location
                loc_elem = card.find('a', class_='location_link') or card.find('div', id=lambda x: x and 'location' in x.lower())
                internship_location = loc_elem.get_text().strip() if loc_elem else location or "Location Not Specified"
                
                # Get stipend
                stipend_elem = card.find('span', class_='stipend') or card.find('div', class_='stipend')
                stipend = stipend_elem.get_text().strip() if stipend_elem else "Unpaid"
                
                # Get duration
                duration_elem = card.find('div', class_='duration') or card.find('div', string=re.compile(r'\d+\s*(week|month)', re.I))
                duration = duration_elem.get_text().strip() if duration_elem else "Duration Not Specified"
                
                # Get apply link
                link_elem = card.find('a', href=re.compile(r'/internship/detail/'))
                if not link_elem:
                    link_elem = card.find('a', class_='view_detail_button')
                
                link = link_elem.get('href', '') if link_elem else ''
                if link and not link.startswith('http'):
                    link = f"https://internshala.com{link}"
                
                if not link:
                    link = search_url
                
                # Get description snippet
                desc_elem = card.find('div', class_='internship_other_details_container')
                if not desc_elem:
                    desc_elem = card.find('div', class_='other_detail_item')
                
                description = desc_elem.get_text().strip()[:200] if desc_elem else "No description available"
                
                # Get start date if available
                start_elem = card.find('div', class_='start-date')
                start_date = start_elem.get_text().strip() if start_elem else None
                
                # Get posted date
                posted_elem = card.find('div', class_='status')
                posted = posted_elem.get_text().strip() if posted_elem else None
                
                internship_data = {
                    "title": title,
                    "company": company,
                    "location": internship_location,
                    "stipend": stipend,
                    "duration": duration,
                    "description": description,
                    "link": link,
                    "source": "Internshala"
                }
                
                if start_date:
                    internship_data["start_date"] = start_date
                if posted:
                    internship_data["posted"] = posted
                
                internships.append(internship_data)
                print(f"    ✓ Internshala: {title[:40]}... at {company}")
                
            except Exception as e:
                print(f"    ✗ Error parsing internship {idx+1}: {e}")
                continue
        
        return internships
        
    except Exception as e:
        print(f"  ❌ Internshala scraping error: {e}")
        import traceback
        traceback.print_exc()
        return []


def scrape_linkedin_internships(role, location, scraperapi_key):
    """Scrape LinkedIn for internships (backup source)"""
    print(f"  💼 Scraping LinkedIn for '{role}' internships...")
    
    try:
        # LinkedIn internship search URL
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(role)}%20internship&location={quote_plus(location)}&f_E=1"
        
        print(f"    📡 Using ScraperAPI to fetch LinkedIn...")
        html_content = scrape_with_scraperapi(search_url, scraperapi_key)
        
        if not html_content:
            print(f"  ❌ Failed to get LinkedIn page")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        internships = []
        
        # Find job cards on LinkedIn
        job_cards = soup.find_all('div', class_='base-card')
        if not job_cards:
            job_cards = soup.find_all('li', class_='jobs-search-results__list-item')
        
        print(f"  ✅ Found {len(job_cards)} LinkedIn internships")
        
        for card in job_cards[:5]:
            try:
                # Get title
                title_elem = card.find('h3', class_='base-search-card__title') or card.find('a', class_='base-card__full-link')
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                
                # Get company
                company_elem = card.find('h4', class_='base-search-card__subtitle') or card.find('a', class_='hidden-nested-link')
                company = company_elem.get_text().strip() if company_elem else "Company Not Listed"
                
                # Get location
                loc_elem = card.find('span', class_='job-search-card__location')
                internship_location = loc_elem.get_text().strip() if loc_elem else location
                
                # Get link
                link_elem = card.find('a', class_='base-card__full-link')
                link = link_elem.get('href', '') if link_elem else ''
                
                if not link:
                    continue
                
                internships.append({
                    "title": title,
                    "company": company,
                    "location": internship_location,
                    "stipend": "Not Specified",
                    "duration": "Not Specified",
                    "description": "Check LinkedIn for details",
                    "link": link,
                    "source": "LinkedIn"
                })
                
                print(f"    ✓ LinkedIn: {title[:40]}... at {company}")
                
            except Exception as e:
                print(f"    ✗ Error parsing LinkedIn internship: {e}")
                continue
        
        return internships
        
    except Exception as e:
        print(f"  ❌ LinkedIn scraping error: {e}")
        return []


def career_agent_task(query, user_profile=None):
    """AI Career Agent - Finds internships using ScraperAPI"""
    print("🎓 AI Career Agent Starting (ScraperAPI)...")
    print(f"Query: {query}")
    
    result = {
        "status": "error",
        "internships": [],
        "message": ""
    }
    
    # Extract role from query
    role = extract_internship_query(query)
    
    # Extract location from query
    location = "India"
    query_lower = query.lower()
    location_keywords = ['in ', ' at ', ' from ']
    for keyword in location_keywords:
        if keyword in query_lower:
            parts = query_lower.split(keyword)
            if len(parts) > 1:
                location = parts[-1].strip()
                role = extract_internship_query(parts[0])
                break
    
    # Use profile skills if available and role is not clear
    if user_profile and (not role or len(role) < 2):
        try:
            if isinstance(user_profile, dict):
                skills = user_profile.get('skills') or user_profile.get('preferred_job_title')
            else:
                skills = user_profile[8] if len(user_profile) > 8 else None
            
            if skills:
                role = skills.split(',')[0].strip() if ',' in str(skills) else str(skills)
        except:
            pass
    
    # Use profile location if available
    if user_profile:
        try:
            if isinstance(user_profile, dict) and user_profile.get('preferred_location'):
                location = user_profile['preferred_location']
            elif isinstance(user_profile, (list, tuple)) and len(user_profile) > 5:
                location = user_profile[5] or location
        except:
            pass
    
    if not role or len(role) < 2:
        result["message"] = "Please specify an internship role. Example: 'find web development internship' or 'python internship in Mumbai'"
        return result
    
    print(f"Searching for: '{role}' internships in '{location}'")
    
    # Get ScraperAPI key
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    if not scraperapi_key:
        print("❌ ERROR: SCRAPERAPI_KEY not found in environment variables!")
        result["message"] = "ScraperAPI key not configured"
        return result
    
    print(f"✅ ScraperAPI Key loaded")
    
    try:
        all_internships = []
        
        # Scrape Internshala (primary source)
        internshala_internships = scrape_internshala_internships(role, location, scraperapi_key)
        all_internships.extend(internshala_internships)
        
        # If Internshala has fewer than 3 results, try LinkedIn as backup
        if len(internshala_internships) < 3:
            print("  ℹ️ Trying LinkedIn as backup source...")
            linkedin_internships = scrape_linkedin_internships(role, location, scraperapi_key)
            all_internships.extend(linkedin_internships)
        
        if not all_internships:
            result["status"] = "error"
            result["message"] = f"No internships found for '{role}' in '{location}'. Try different keywords like 'python', 'web development', 'marketing', etc."
            result["suggestion"] = "Try broader terms or different locations"
            print("⚠️ No internships found")
            return result
        
        # Filter and prioritize paid internships
        paid_internships = [i for i in all_internships if 'unpaid' not in i['stipend'].lower()]
        
        # Get top 3: prioritize paid internships
        if len(paid_internships) >= 3:
            top_internships = paid_internships[:3]
        else:
            top_internships = all_internships[:3]
        
        result["status"] = "success"
        result["internships"] = top_internships
        result["total_found"] = len(all_internships)
        result["query"] = role
        result["location"] = location
        result["message"] = f"🎉 Found {len(all_internships)} internships for '{role}' in '{location}'! Showing TOP 3"
        
        print(f"\n✅ Found {len(all_internships)} total internships")
        print(f"🎯 TOP INTERNSHIP: {top_internships[0]['title'][:50]}... at {top_internships[0]['company']}")
        
        # Print top 3 for verification
        print("\n=== TOP 3 INTERNSHIPS ===")
        for i, internship in enumerate(top_internships, 1):
            print(f"\n{i}. {internship['title']}")
            print(f"   Company: {internship['company']}")
            print(f"   Location: {internship['location']}")
            print(f"   Stipend: {internship['stipend']}")
            print(f"   Apply: {internship['link']}")
        
        return result
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Error searching internships: {str(e)}"
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return result
