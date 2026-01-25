import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


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


def scrape_amazon_products(query):
    """Scrape Amazon India for products"""
    print("  🔍 Scraping Amazon India...")
    
    try:
        # Amazon search URL
        search_url = f"https://www.amazon.in/s?k={quote_plus(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(search_url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"  ❌ Amazon returned status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        
        # Find product cards - Amazon uses these classes
        product_divs = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        print(f"  ✅ Found {len(product_divs)} Amazon products")
        
        for div in product_divs[:10]:
            try:
                # Get title
                title_elem = div.find('h2', class_='a-size-mini')
                if not title_elem:
                    title_elem = div.find('span', class_='a-size-medium')
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                
                if not title or len(title) < 5:
                    continue
                
                # Get price
                price_elem = div.find('span', class_='a-price-whole')
                if not price_elem:
                    continue
                
                price_text = price_elem.get_text().strip()
                price = extract_price(price_text)
                
                if price == float('inf') or price == 0:
                    continue
                
                # Get DIRECT product link
                link_elem = div.find('a', class_='a-link-normal')
                if not link_elem or not link_elem.get('href'):
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


def scrape_flipkart_products(query):
    """Scrape Flipkart for products"""
    print("  🔍 Scraping Flipkart...")
    
    try:
        # Flipkart search URL
        search_url = f"https://www.flipkart.com/search?q={quote_plus(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(search_url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"  ❌ Flipkart returned status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        
        # Find product cards - Flipkart uses these classes
        product_divs = soup.find_all('div', class_='_1AtVbE')
        if not product_divs:
            # Try alternate class
            product_divs = soup.find_all('div', class_='_4ddWXP')
        
        print(f"  ✅ Found {len(product_divs)} Flipkart products")
        
        for div in product_divs[:10]:
            try:
                # Get title
                title_elem = div.find('a', class_='IRpwTa') or div.find('div', class_='_4rR01T')
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                
                if not title or len(title) < 5:
                    continue
                
                # Get price
                price_elem = div.find('div', class_='_30jeq3')
                if not price_elem:
                    continue
                
                price_text = price_elem.get_text().strip()
                price = extract_price(price_text)
                
                if price == float('inf') or price == 0:
                    continue
                
                # Get DIRECT product link
                link_elem = div.find('a', class_='_1fQZEK') or div.find('a', class_='IRpwTa')
                if not link_elem or not link_elem.get('href'):
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
    """AI Shopping Assistant using Web Scraping"""
    print("🛒 AI Shopping Assistant Starting (Web Scraper)...")
    print(f"Query: {query}")
    
    # Clean the query
    product_query = query.lower()
    product_query = re.sub(r'\b(find|search|buy|order|get|purchase|best|top)\b', '', product_query).strip()
    product_query = re.sub(r'\s+', ' ', product_query)
    
    print(f"Cleaned query: {product_query}")
    
    try:
        all_products = []
        
        # Scrape Amazon
        amazon_products = scrape_amazon_products(product_query)
        all_products.extend(amazon_products)
        
        # Scrape Flipkart
        flipkart_products = scrape_flipkart_products(product_query)
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
        
        # Create summary
        top_3_summary = "\n".join([
            f"{i+1}. {p['title'][:60]} - {p['price_text']} ({p['site']})"
            for i, p in enumerate(all_products[:3])
        ])
        
        return {
            "status": "success",
            "best_deal": all_products[0],
            "top_products": all_products[:5],
            "total_products": len(all_products),
            "message": f"🎉 Found {len(all_products)} products!\n\n🏆 TOP 3 DEALS:\n{top_3_summary}",
            "query": product_query
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}
