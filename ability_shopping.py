import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlencode


def extract_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return float('inf')
    # Handle different formats
    clean = str(price_text).replace('₹', '').replace('Rs', '').replace('$', '').replace(',', '').replace(' ', '')
    # Remove any non-numeric characters except decimal point
    clean = re.sub(r'[^\d.]', '', clean)
    try:
        return float(clean)
    except:
        return float('inf')


def scrape_with_scraperapi(url, api_key):
    """Use ScraperAPI to bypass anti-bot protection"""
    try:
        # ScraperAPI endpoint
        scraperapi_url = 'http://api.scraperapi.com'
        
        params = {
            'api_key': api_key,
            'url': url,
            'country_code': 'in'  # India
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


def scrape_amazon_products(query, scraperapi_key):
    """Scrape Amazon India for products using ScraperAPI"""
    print("  🔍 Scraping Amazon India...")
    
    try:
        # Amazon search URL
        search_url = f"https://www.amazon.in/s?k={quote_plus(query)}"
        
        print(f"    📡 Using ScraperAPI to fetch Amazon...")
        html_content = scrape_with_scraperapi(search_url, scraperapi_key)
        
        if not html_content:
            print(f"  ❌ Failed to get Amazon page")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Find product cards - Amazon uses these classes
        product_divs = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        print(f"  ✅ Found {len(product_divs)} Amazon products")
        
        for div in product_divs[:10]:
            try:
                # Get title - Try multiple selectors
                title_elem = (
                    div.find('h2', class_='a-size-mini') or
                    div.find('span', class_='a-size-medium') or
                    div.find('h2', class_='a-size-base-plus') or
                    div.find('span', class_='a-size-base-plus') or
                    div.find('h2') or  # Any h2
                    div.find('span', class_='a-text-normal')
                )
                
                if not title_elem:
                    # Try finding by data-component-type
                    title_link = div.find('a', {'class': 's-underline-text'})
                    if title_link:
                        title_elem = title_link.find('span')
                
                if not title_elem:
                    print(f"    ✗ Product: No title found (tried all selectors)")
                    continue
                
                title = title_elem.get_text().strip()
                
                if not title or len(title) < 5:
                    print(f"    ✗ Product: Title too short: {title}")
                    continue
                
                print(f"    🔍 Found title: {title[:40]}...")
                
                # Get price - Try multiple selectors
                price_elem = (
                    div.find('span', class_='a-price-whole') or
                    div.find('span', class_='a-offscreen')
                )
                
                if not price_elem:
                    print(f"    ✗ Product {title[:30]}: No price found")
                    continue
                
                price_text = price_elem.get_text().strip()
                price = extract_price(price_text)
                
                if price == float('inf') or price == 0:
                    print(f"    ✗ Product {title[:30]}: Invalid price: {price_text}")
                    continue
                
                print(f"    💰 Found price: ₹{int(price):,}")
                
                # Get DIRECT product link - Try multiple methods
                link_elem = (
                    div.find('a', class_='a-link-normal') or
                    div.find('a', {'class': 's-underline-text'}) or
                    div.find('a', href=True)
                )
                
                if not link_elem or not link_elem.get('href'):
                    print(f"    ✗ Product {title[:30]}: No link found")
                    continue
                
                link = link_elem['href']
                
                # Make it a full URL
                if link.startswith('/'):
                    link = f"https://www.amazon.in{link}"
                elif not link.startswith('http'):
                    link = f"https://www.amazon.in/{link}"
                
                # Get rating
                rating_elem = div.find('span', class_='a-icon-alt')
                rating = 0
                if rating_elem:
                    rating_text = rating_elem.get_text()
                    rating_match = re.search(r'([\d.]+)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Get reviews count
                reviews_elem = div.find('span', {'class': 'a-size-base', 'dir': 'auto'})
                reviews = 0
                if reviews_elem:
                    reviews_text = reviews_elem.get_text()
                    reviews_match = re.search(r'([\d,]+)', reviews_text)
                    if reviews_match:
                        reviews = int(reviews_match.group(1).replace(',', ''))
                
                products.append({
                    "site": "Amazon",
                    "title": title,
                    "price": price,
                    "price_text": f"₹{int(price):,}",
                    "link": link,
                    "rating": rating,
                    "reviews": reviews
                })
                
                print(f"    ✓ Amazon: {title[:50]}... - ₹{int(price):,}")
                
            except Exception as e:
                print(f"    ✗ Error parsing Amazon product: {e}")
                continue
        
        return products
        
    except Exception as e:
        print(f"  ❌ Amazon scraping error: {e}")
        import traceback
        traceback.print_exc()
        return []


def scrape_flipkart_products(query, scraperapi_key):
    """Scrape Flipkart for products using ScraperAPI"""
    print("  🔍 Scraping Flipkart...")
    
    try:
        # Flipkart search URL
        search_url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
        
        print(f"    📡 Using ScraperAPI to fetch Flipkart...")
        html_content = scrape_with_scraperapi(search_url, scraperapi_key)
        
        if not html_content:
            print(f"  ❌ Failed to get Flipkart page")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Find product cards - Flipkart uses multiple possible classes
        product_divs = (
            soup.find_all('div', class_='_1AtVbE') or
            soup.find_all('div', class_='_4ddWXP') or
            soup.find_all('div', class_='_2kHMtA') or
            soup.find_all('div', class_='_13oc-S') or
            soup.find_all('div', {'data-id': True})  # Products have data-id attribute
        )
        
        print(f"  ✅ Found {len(product_divs)} Flipkart products")
        
        # DEBUG: Print first product HTML to see structure
        if product_divs and len(product_divs) > 0:
            print(f"  🔍 DEBUG - First product classes: {product_divs[0].get('class')}")
            # Find all 'a' tags in first product
            links = product_divs[0].find_all('a', limit=3)
            if links:
                print(f"  🔍 DEBUG - Found {len(links)} links in first product")
                for i, link in enumerate(links[:2]):
                    print(f"    Link {i+1} text: {link.get_text()[:50] if link.get_text() else 'NO TEXT'}")
        
        for div in product_divs[:10]:
            try:
                # Get title - Try multiple selectors
                title_elem = (
                    div.find('a', class_='IRpwTa') or
                    div.find('div', class_='_4rR01T') or
                    div.find('a', class_='s1Q9rs') or
                    div.find('a', class_='_2rpwqI') or
                    div.find('div', class_='_2WkVRV')
                )
                
                if not title_elem:
                    print(f"    ✗ Product: No title found")
                    continue
                
                title = title_elem.get_text().strip()
                
                if not title or len(title) < 5:
                    print(f"    ✗ Product: Title too short: {title}")
                    continue
                
                print(f"    🔍 Found title: {title[:40]}...")
                
                # Get price - Try multiple selectors
                price_elem = (
                    div.find('div', class_='_30jeq3') or
                    div.find('div', class_='_25b18c') or
                    div.find('div', class_='_1_WHN1')
                )
                
                if not price_elem:
                    print(f"    ✗ Product {title[:30]}: No price found")
                    continue
                
                price_text = price_elem.get_text().strip()
                price = extract_price(price_text)
                
                if price == float('inf') or price == 0:
                    print(f"    ✗ Product {title[:30]}: Invalid price: {price_text}")
                    continue
                
                print(f"    💰 Found price: ₹{int(price):,}")
                
                # Get DIRECT product link - Try multiple methods
                link_elem = (
                    div.find('a', class_='_1fQZEK') or
                    div.find('a', class_='IRpwTa') or
                    div.find('a', class_='s1Q9rs') or
                    div.find('a', class_='_2rpwqI') or
                    div.find('a', href=True)
                )
                
                if not link_elem or not link_elem.get('href'):
                    print(f"    ✗ Product {title[:30]}: No link found")
                    continue
                
                link = link_elem['href']
                
                # Make it a full URL
                if link.startswith('/'):
                    link = f"https://www.flipkart.com{link}"
                elif not link.startswith('http'):
                    link = f"https://www.flipkart.com/{link}"
                
                # Get rating
                rating_elem = div.find('div', class_='_3LWZlK')
                rating = 0
                if rating_elem:
                    rating_text = rating_elem.get_text()
                    rating_match = re.search(r'([\d.]+)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Get reviews count
                reviews_elem = div.find('span', class_='_2_R_DZ')
                reviews = 0
                if reviews_elem:
                    reviews_text = reviews_elem.get_text()
                    reviews_match = re.search(r'([\d,]+)', reviews_text)
                    if reviews_match:
                        reviews = int(reviews_match.group(1).replace(',', ''))
                
                products.append({
                    "site": "Flipkart",
                    "title": title,
                    "price": price,
                    "price_text": f"₹{int(price):,}",
                    "link": link,
                    "rating": rating,
                    "reviews": reviews
                })
                
                print(f"    ✓ Flipkart: {title[:50]}... - ₹{int(price):,}")
                
            except Exception as e:
                print(f"    ✗ Error parsing Flipkart product: {e}")
                continue
        
        return products
        
    except Exception as e:
        print(f"  ❌ Flipkart scraping error: {e}")
        import traceback
        traceback.print_exc()
        return []


def shopping_assistant_task(query, user_profile=None):
    """AI Shopping Assistant using ScraperAPI"""
    print("🛒 AI Shopping Assistant Starting (ScraperAPI)...")
    print(f"Query: {query}")
    
    # Clean the query
    product_query = query.lower()
    product_query = re.sub(r'\b(find|search|buy|order|get|purchase|best|top)\b', '', product_query).strip()
    product_query = re.sub(r'\s+', ' ', product_query)
    
    print(f"Cleaned query: {product_query}")
    
    # Get ScraperAPI key
    scraperapi_key = os.environ.get('SCRAPERAPI_KEY', '').strip()
    if not scraperapi_key:
        print("❌ ERROR: SCRAPERAPI_KEY not found in environment variables!")
        return {"status": "error", "message": "ScraperAPI key not configured"}
    
    print(f"✅ ScraperAPI Key loaded")
    
    try:
        all_products = []
        
        # Scrape Amazon
        amazon_products = scrape_amazon_products(product_query, scraperapi_key)
        all_products.extend(amazon_products)
        
        # Scrape Flipkart
        flipkart_products = scrape_flipkart_products(product_query, scraperapi_key)
        all_products.extend(flipkart_products)
        
        if not all_products:
            print("⚠️ No products found on Amazon or Flipkart")
            return {
                "status": "error", 
                "message": f"No products found for '{product_query}'. Try a different search term.",
                "suggestion": "Try simpler terms like 'laptop', 'iPhone', 'headphones'"
            }
        
        # Sort by price - cheapest first
        all_products.sort(key=lambda x: x['price'])
        
        print(f"\n✅ Found {len(all_products)} total products")
        print(f"🎯 BEST DEAL: {all_products[0]['title'][:50]}... - {all_products[0]['price_text']} ({all_products[0]['site']})")
        
        # Create summary - TOP 5 not TOP 3!
        top_5_summary = "\n".join([
            f"{i+1}. {p['title'][:60]} - {p['price_text']} ({p['site']})"
            for i, p in enumerate(all_products[:5])
        ])
        
        return {
            "status": "success",
            "best_deal": all_products[0],
            "top_products": all_products[:5],
            "total_products": len(all_products),
            "message": f"🎉 Found {len(all_products)} products!\n\n🏆 TOP 5 DEALS:\n{top_5_summary}",
            "query": product_query
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}

