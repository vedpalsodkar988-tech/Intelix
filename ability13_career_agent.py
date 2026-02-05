import os
import re
import requests
from bs4 import BeautifulSoup

def career_agent_task(query, user_profile=None):
    """
    AI Career Agent - Finds internships on Internshala
    FIXED: Now properly extracts role from query
    """
    print(f"🎓 AI Career Agent Starting...")
    print(f"Original query: {query}")
    
    # CRITICAL FIX: Extract the actual role from the query
    # Remove common words like "find", "search", "internship", "internships", etc.
    clean_query = query.lower()
    
    # Remove these words
    remove_words = [
        'find', 'search', 'get', 'show', 'looking for', 'look for',
        'internship', 'internships', 'intern', 'for', 'in', 'at',
        'give me', 'get me', 'i want', 'i need'
    ]
    
    for word in remove_words:
        clean_query = re.sub(r'\b' + word + r'\b', '', clean_query, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    # If query is now empty, use default
    if not clean_query:
        clean_query = "web development"
    
    print(f"✅ Cleaned query for Internshala: '{clean_query}'")
    
    # Get ScraperAPI key
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    if not scraperapi_key:
        return {"status": "error", "message": "ScraperAPI key not configured"}
    
    try:
        # Build Internshala search URL
        # Format: https://internshala.com/internships/web-development-internship
        search_term = clean_query.replace(' ', '-')
        internshala_url = f"https://internshala.com/internships/{search_term}-internship"
        
        print(f"🔍 Searching Internshala: {internshala_url}")
        
        # Use ScraperAPI to scrape
        api_url = f"http://api.scraperapi.com?api_key={scraperapi_key}&url={internshala_url}"
        
        response = requests.get(api_url, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Internshala returned status: {response.status_code}")
            return {
                "status": "error",
                "message": f"Could not fetch internships. Try a different search term."
            }
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find internship cards
        internship_cards = soup.find_all('div', class_='individual_internship')
        
        if not internship_cards:
            # Try alternative class names
            internship_cards = soup.find_all('div', class_='internship_meta')
        
        internships = []
        
        for card in internship_cards[:3]:  # TOP 3 only
            try:
                # Extract title
                title_elem = card.find('h3') or card.find('h4') or card.find('a', class_='view_detail_button')
                title = title_elem.get_text(strip=True) if title_elem else "Internship"
                
                # Extract company
                company_elem = card.find('p', class_='company_name') or card.find('a', class_='link_display_like_text')
                company = company_elem.get_text(strip=True) if company_elem else "Company Not Listed"
                
                # Extract location
                location_elem = card.find('div', id=lambda x: x and 'location' in x) or card.find('p', class_='location_link')
                location = location_elem.get_text(strip=True) if location_elem else "India"
                
                # Extract duration
                duration_elem = card.find('div', class_='item_logo_duration') or card.find('span', string=re.compile('duration', re.I))
                duration = duration_elem.get_text(strip=True) if duration_elem else "Duration Not Specified"
                
                # Extract stipend
                stipend_elem = card.find('span', class_='stipend') or card.find('div', class_='item_logo_stipend')
                stipend = stipend_elem.get_text(strip=True) if stipend_elem else "Competitive stipend"
                
                # Extract link
                link_elem = card.find('a', class_='view_detail_button') or card.find('a', href=re.compile('/internship/detail/'))
                link = "https://internshala.com" + link_elem['href'] if link_elem and link_elem.get('href') else None
                
                # Extract description
                desc_elem = card.find('div', class_='internship_other_details_container') or card.find('p')
                description = desc_elem.get_text(strip=True)[:200] if desc_elem else "No description available"
                
                internship = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "duration": duration,
                    "stipend": stipend,
                    "description": description,
                    "link": link,
                    "source": "Internshala"
                }
                
                internships.append(internship)
                print(f"✅ Found: {title} at {company}")
                
            except Exception as e:
                print(f"⚠️ Error parsing internship card: {e}")
                continue
        
        if not internships:
            return {
                "status": "error",
                "message": f"No internships found for '{clean_query}'. Try different keywords like 'marketing', 'design', 'content writing'."
            }
        
        print(f"🎉 Found {len(internships)} internships!")
        
        return {
            "status": "success",
            "internships": internships,
            "total_found": len(internships),
            "query": clean_query,
            "message": f"🎓 Found {len(internships)} internships for '{clean_query}' in India! Showing TOP 3:"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to search internships: {str(e)}"
        }
