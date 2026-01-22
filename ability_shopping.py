import requests
import os
import re


def extract_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return float('inf')
    # Handle different formats
    clean = str(price_text).replace('₹', '').replace('Rs', '').replace('$', '').replace(',', '').replace(' ', '')
    try:
        return float(clean)
    except:
        return float('inf')


def shopping_assistant_task(query, user_profile=None):
    """AI Shopping Assistant using RapidAPI Real-Time Product Search"""
    print("🛒 AI Shopping Assistant Starting (RapidAPI)...")
    print(f"Query: {query}")
    
    # Clean the query
    product_query = re.sub(r'\b(find|search|buy|order|get|purchase|best|top|under)\b', '', query.lower()).strip()
    product_query = re.sub(r'\s+', ' ', product_query)
    print(f"Cleaned query: {product_query}")
    
    # Get API key from environment - strip whitespace
    api_key = os.environ.get('RAPIDAPI_KEY', '').strip()
    if not api_key:
        print("❌ ERROR: RAPIDAPI_KEY not found in environment variables!")
        return {"status": "error", "message": "API key not configured"}
    
    print(f"✅ API Key loaded (length: {len(api_key)} chars)")
    
    try:
        # CORRECTED ENDPOINT - Using the right path
        url = "https://real-time-product-search.p.rapidapi.com/search"
        
        headers = {
            "x-rapidapi-key": api_key,  # Changed to lowercase 'x'
            "x-rapidapi-host": "real-time-product-search.p.rapidapi.com"  # Changed to lowercase 'x'
        }
        
        # Updated parameters based on API docs
        params = {
            "q": product_query,
            "country": "in",
            "language": "en",
            "limit": "20"  # Get more results
        }
        
        print(f"📡 Calling RapidAPI with query: '{product_query}'...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 404:
            print("❌ 404 Error - API endpoint not found")
            print("This might mean:")
            print("1. Your subscription doesn't include this API")
            print("2. The API endpoint has changed")
            print("Please check your RapidAPI subscription")
            return {"status": "error", "message": "API endpoint not found. Check your RapidAPI subscription."}
        
        if response.status_code == 403:
            print("❌ 403 Error - Access forbidden")
            return {"status": "error", "message": "API key invalid or subscription inactive"}
        
        if response.status_code != 200:
            print(f"❌ API Error: Status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return {"status": "error", "message": f"API error: {response.status_code}"}
        
        data = response.json()
        print(f"✅ API Response received")
        
        # Debug: Print response structure
        print(f"Response keys: {list(data.keys())}")
        
        # Parse results - Real-Time Product Search returns data in 'data' field
        products = []
        
        if 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
            print(f"Found {len(data['data'])} products from API")
            
            for idx, item in enumerate(data['data'][:20]):
                try:
                    # Extract product details - adapting to actual API response
                    title = item.get('product_title', '') or item.get('title', '')
                    if not title or len(title) < 5:
                        continue
                    
                    # Try multiple price fields
                    price_text = None
                    if 'offer' in item and isinstance(item['offer'], dict):
                        price_text = item['offer'].get('price')
                    if not price_text:
                        price_text = item.get('product_price') or item.get('price')
                    
                    if not price_text:
                        print(f"  ✗ Item {idx+1}: No price found")
                        continue
                    
                    price = extract_price(price_text)
                    if price == float('inf') or price == 0:
                        continue
                    
                    # Get merchant/site
                    site = "Online Store"
                    if 'offer' in item and isinstance(item['offer'], dict):
                        site = item['offer'].get('store_name', 'Online Store')
                    
                    # Detect Amazon/Flipkart
                    if 'amazon' in str(site).lower():
                        site = "Amazon"
                    elif 'flipkart' in str(site).lower():
                        site = "Flipkart"
                    
                    # Get product link
                    link = item.get('product_page_url', '')
                    if not link and 'offer' in item and isinstance(item['offer'], dict):
                        link = item['offer'].get('offer_page_url', '')
                    
                    if not link or not link.startswith('http'):
                        continue
                    
                    products.append({
                        "site": site,
                        "title": title,
                        "price": price,
                        "price_text": f"₹{int(price):,}",
                        "link": link
                    })
                    
                    print(f"  ✓ Item {idx+1}: {title[:50]}... - ₹{int(price):,} ({site})")
                    
                except Exception as e:
                    print(f"  ✗ Error parsing item {idx+1}: {e}")
                    continue
        else:
            print(f"⚠️ Unexpected API response structure")
            print(f"Response: {str(data)[:500]}")
        
        if not products:
            print("⚠️ No products found in API response")
            return {
                "status": "error", 
                "message": "No products found. Try a different search term.",
                "debug_info": f"API returned {len(data.get('data', []))} items but none were parseable"
            }
        
        # Sort by price - cheapest first
        products.sort(key=lambda x: x['price'])
        
        print(f"\n✅ Found {len(products)} valid products")
        print(f"🎯 BEST DEAL: {products[0]['title'][:50]}... - {products[0]['price_text']} ({products[0]['site']})")
        
        return {
            "status": "success",
            "best_deal": products[0],
            "top_products": products[:5],  # Return top 5 instead of 3
            "total_products": len(products),
            "message": f"Found {len(products)} products! Best deal: {products[0]['price_text']}"
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
