import requests
import os
import re


def extract_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return float('inf')
    # Handle different formats
    clean = str(price_text).replace('₹', '').replace('Rs', '').replace(',', '').replace(' ', '')
    try:
        return float(clean)
    except:
        return float('inf')


def shopping_assistant_task(query, user_profile=None):
    """AI Shopping Assistant using RapidAPI"""
    print("🛒 AI Shopping Assistant Starting (RapidAPI)...")
    print(f"Query: {query}")
    
    # Clean the query
    product_query = re.sub(r'\b(find|search|buy|order|get|purchase|best|top)\b', '', query.lower()).strip()
    product_query = re.sub(r'\s+', ' ', product_query)
    print(f"Cleaned query: {product_query}")
    
    # Get API key from environment
    api_key = os.environ.get('RAPIDAPI_KEY')
    if not api_key:
        print("❌ ERROR: RAPIDAPI_KEY not found in environment variables!")
        return {"status": "error", "message": "API key not configured"}
    
    try:
        # Call RapidAPI Real-Time Product Search
        url = "https://real-time-product-search.p.rapidapi.com/search"
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
        }
        
        params = {
            "q": product_query,
            "country": "in",
            "language": "en"
        }
        
        print("📡 Calling RapidAPI...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API Error: Status {response.status_code}")
            return {"status": "error", "message": f"API error: {response.status_code}"}
        
        data = response.json()
        print(f"✅ API Response received")
        
        # Parse results
        products = []
        
        if 'data' in data and data['data']:
            print(f"Found {len(data['data'])} products from API")
            
            for idx, item in enumerate(data['data'][:10]):
                try:
                    # Extract product details
                    title = item.get('product_title', '')
                    if not title or len(title) < 5:
                        continue
                    
                    # Get price
                    price_text = None
                    if 'offer' in item and 'price' in item['offer']:
                        price_text = item['offer']['price']
                    elif 'product_price' in item:
                        price_text = item['product_price']
                    
                    if not price_text:
                        continue
                    
                    price = extract_price(price_text)
                    if price == float('inf') or price == 0:
                        continue
                    
                    # Get merchant/site
                    site = "Online Store"
                    if 'offer' in item and 'store_name' in item['offer']:
                        site = item['offer']['store_name']
                    
                    # Detect Amazon/Flipkart
                    if 'amazon' in site.lower():
                        site = "Amazon"
                    elif 'flipkart' in site.lower():
                        site = "Flipkart"
                    
                    # Get product link
                    link = item.get('product_page_url', '')
                    if not link:
                        link = item.get('offer', {}).get('offer_page_url', '')
                    
                    if not link or not link.startswith('http'):
                        continue
                    
                    products.append({
                        "site": site,
                        "title": title,
                        "price": price,
                        "price_text": f"₹{int(price):,}",
                        "link": link
                    })
                    
                    print(f"✓ Item {idx+1}: {title[:50]}... - ₹{int(price):,} ({site})")
                    
                except Exception as e:
                    print(f"✗ Error parsing item {idx+1}: {e}")
                    continue
        
        if not products:
            print("⚠️ No products found in API response")
            return {"status": "error", "message": "No products found"}
        
        # Sort by price - cheapest first
        products.sort(key=lambda x: x['price'])
        
        print(f"\n✅ Found {len(products)} valid products")
        print(f"🎯 BEST DEAL: {products[0]['title'][:50]}... - {products[0]['price_text']} ({products[0]['site']})")
        
        return {
            "status": "success",
            "best_deal": products[0],
            "top_products": products[:3],
            "total_products": len(products),
            "message": "Shopping completed!"
        }
        
    except requests.exceptions.Timeout:
        print("❌ API request timed out")
        return {"status": "error", "message": "Request timed out"}
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return {"status": "error", "message": f"Network error: {str(e)}"}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}
