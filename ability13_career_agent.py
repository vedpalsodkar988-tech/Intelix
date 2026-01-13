from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import re

def extract_internship_query(query):
    """Extract internship role from query"""
    query_lower = query.lower()
    
    # Remove command words
    role = query_lower
    remove_words = ['find', 'search', 'get', 'looking for', 'internship', 'internships', 'for', 'in']
    for word in remove_words:
        role = role.replace(word, ' ')
    
    role = ' '.join(role.split()).strip()
    
    return role


def career_agent_task(query, user_profile=None):
    """AI Career Agent - Finds internships on Internshala"""
    print("AI Career Agent Starting...")
    print(f"Query: {query}")
    
    result = {
        "status": "error",
        "internships": [],
        "message": ""
    }
    
    # Extract role from query
    role = extract_internship_query(query)
    
    # Use profile skills if available
    if user_profile and (not role or len(role) < 2):
        try:
            skills = user_profile[8] if len(user_profile) > 8 else None
            if skills:
                role = skills.split(',')[0].strip()
        except:
            pass
    
    if not role or len(role) < 2:
        result["message"] = "Please specify an internship role. Example: 'find web development internship'"
        return result
    
    print(f"Role: {role}")
    
    # Search Internshala
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # CHANGED: Now runs in background
            args=['--start-maximized']
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        
        try:
            # Build Internshala search URL
            search_query = role.replace(' ', '-')
            internshala_url = f"https://internshala.com/internships/{search_query}-internship"
            
            print(f"Opening Internshala: {internshala_url}")
            page.goto(internshala_url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(4000)
            
            # Close any popups
            try:
                page.locator('button:has-text("Close"), .close, .modal-close').first.click(timeout=2000)
            except:
                pass
            
            page.wait_for_timeout(2000)
            
            # Extract internship listings
            print("Extracting internships...")
            
            # Wait for internship cards
            try:
                page.wait_for_selector('.internship_meta, .individual_internship', timeout=10000)
            except:
                print("Internship cards taking time to load...")
            
            page.wait_for_timeout(2000)
            
            # Get internship cards
            internship_cards = page.locator('.internship_meta, .individual_internship').all()[:10]
            
            print(f"Found {len(internship_cards)} internship listings")
            
            internships_found = []
            
            for idx, card in enumerate(internship_cards):
                try:
                    # Extract title/role
                    try:
                        title_elem = card.locator('.profile, h3, h4, .job-internship-name').first
                        title = title_elem.inner_text(timeout=2000).strip()
                    except:
                        continue
                    
                    # Extract company
                    try:
                        company_elem = card.locator('.company-name, .company_name, .link_display_like_text').first
                        company = company_elem.inner_text(timeout=2000).strip()
                    except:
                        company = "Company not listed"
                    
                    # Extract location
                    try:
                        location_elem = card.locator('.location_link, .locations, .location').first
                        location = location_elem.inner_text(timeout=2000).strip()
                    except:
                        location = "Location not specified"
                    
                    # Extract stipend
                    try:
                        stipend_elem = card.locator('.stipend, .stipend-text').first
                        stipend = stipend_elem.inner_text(timeout=2000).strip()
                    except:
                        stipend = "Unpaid"
                    
                    # Extract duration
                    try:
                        duration_elem = card.locator('.duration, .duration-text').first
                        duration = duration_elem.inner_text(timeout=2000).strip()
                    except:
                        duration = "Duration not specified"
                    
                    # Extract apply link
                    try:
                        link_elem = card.locator('a[href*="detail"]').first
                        link = link_elem.get_attribute('href', timeout=2000)
                        if link and not link.startswith('http'):
                            link = 'https://internshala.com' + link
                    except:
                        link = internshala_url
                    
                    # Extract description snippet
                    try:
                        desc_elem = card.locator('.internship_other_details_container, .other_detail_item_link').first
                        description = desc_elem.inner_text(timeout=2000)[:150]
                    except:
                        description = "No description available"
                    
                    internship_data = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "stipend": stipend,
                        "duration": duration,
                        "description": description,
                        "link": link
                    }
                    
                    internships_found.append(internship_data)
                    print(f"Internship {idx+1}: {title} at {company}")
                    
                except Exception as e:
                    print(f"Skipping internship {idx+1}: {e}")
                    continue
            
            if internships_found:
                # Filter TOP 3 (prioritize paid internships)
                paid_internships = [i for i in internships_found if 'unpaid' not in i['stipend'].lower()]
                if len(paid_internships) >= 3:
                    top_3 = paid_internships[:3]
                else:
                    top_3 = internships_found[:3]
                
                result["status"] = "success"
                result["internships"] = top_3
                result["total_found"] = len(internships_found)
                result["message"] = f"Found {len(internships_found)} internships. Showing TOP 3!"
                print(f"\nSuccessfully found {len(internships_found)} internships! Filtered to TOP 3")
                
                # Print the top 3 for verification
                print("\n=== TOP 3 INTERNSHIPS ===")
                for i, internship in enumerate(top_3, 1):
                    print(f"\n{i}. {internship['title']}")
                    print(f"   Company: {internship['company']}")
                    print(f"   Location: {internship['location']}")
                    print(f"   Stipend: {internship['stipend']}")
                    print(f"   Apply: {internship['link']}")
            else:
                result["status"] = "error"
                result["message"] = f"No internships found for '{role}'. Try different keywords."
            
            # REMOVED: Browser blocking line - now returns immediately
            
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Error searching internships: {str(e)}"
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()
    
    return result