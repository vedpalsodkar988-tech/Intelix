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


def get_direct_merchant_link(serpapi_url, api_key):
    """Get direct merchant link from SerpAPI immersive product page"""
    try:
        response = requests.get(serpapi_url, params={"api_key": api_key}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Try to find direct merchant link in offers
            if 'sellers_results' in data and data['sellers_results']:
                # Get first seller (usually best price)
                first_seller = data['sellers_results'][0]
                return first_seller.get('link') or first_seller.get('offer_link')
            elif 'offers' in data and data['offers']:
                first_offer = data['offers'][0]
                return first_offer.get('link') or first_offer.get('offer_link')
        return None
    except Exception as e:
        print(f"  ⚠️ Failed to get direct link: {e}")
        return None


def shopping_assistant_task(query, user_profile=None):
    """AI Shopping Assistant using SerpAPI Google Shopping"""
    print("🛒 AI Shopping Assistant Starting (SerpAPI)...")
    print(f"Query: {query}")
    
    # Clean the query - keep price ranges
    product_query = query.lower()
    # Remove action words but keep product and price info
    product_query = re.sub(r'\b(find|search|buy|order|get|purchase|best|top)\b', '', product_query).strip()
    product_query = re.sub(r'\s+', ' ', product_query)
    
    # If query has "under" price, convert to better format for shopping
    # Example: "laptop under 50000" -> "laptop under 50000 rupees"
    if 'under' in product_query and not any(word in product_query for word in ['rupees', 'rs', '₹', 'inr']):
        product_query = product_query + " rupees"
    
    print(f"Cleaned query: {product_query}")
    
    # Get API key from environment
    api_key = os.environ.get('SERPAPI_KEY', '').strip()
    if not api_key:
        print("❌ ERROR: SERPAPI_KEY not found in environment variables!")
        return {"status": "error", "message": "SerpAPI key not configured"}
    
    print(f"✅ SerpAPI Key loaded")
    
    try:
        # SerpAPI Google Shopping endpoint
        url = "https://serpapi.com/search"
        
        params = {
            "engine": "google_shopping",
            "q": product_query,
            "api_key": api_key,
            "location": "Delhi, India",  # More specific location
            "hl": "en",
            "gl": "in",
            "num": "30",  # Get more results
            "no_cache": "true"  # Don't use cached results
        }
        
        print(f"📡 Calling SerpAPI Google Shopping with query: '{product_query}'...")
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ 401 Error - Invalid API key")
            return {"status": "error", "message": "SerpAPI key is invalid"}
        
        if response.status_code == 403:
            print("❌ 403 Error - API limit exceeded or account inactive")
            return {"status": "error", "message": "SerpAPI limit exceeded or account inactive"}
        
        if response.status_code != 200:
            print(f"❌ API Error: Status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return {"status": "error", "message": f"API error: {response.status_code}"}
        
        data = response.json()
        print(f"✅ SerpAPI Response received")
        
        # Parse results
        products = []
        
        # SerpAPI returns results in 'shopping_results' field
        if 'shopping_results' in data and len(data['shopping_results']) > 0:
            print(f"Found {len(data['shopping_results'])} products from Google Shopping")
            
            # DEBUG: Print first item structure to see actual fields
            print("\n🔍 DEBUG - First item structure:")
            first_item = data['shopping_results'][0]
            print(f"Available fields: {list(first_item.keys())}")
            # Check if offers exist
            if 'offers' in first_item:
                print(f"✅ Offers found: {first_item['offers']}")
            else:
                print(f"⚠️ No 'offers' field in response")
            print("=" * 80)
            
            for idx, item in enumerate(data['shopping_results'][:20]):
                try:
                    # Extract product details
                    title = item.get('title', '')
                    if not title or len(title) < 5:
                        print(f"  ✗ Item {idx+1}: No title")
                        continue
                    
                    # Get price - SerpAPI provides clean price data
                    # Try multiple price fields
                    price = None
                    
                    # Method 1: Direct extracted_price (most reliable)
                    if 'extracted_price' in item and item['extracted_price']:
                        price = float(item['extracted_price'])
                    
                    # Method 2: Price field
                    elif 'price' in item and item['price']:
                        price_text = item['price']
                        price = extract_price(price_text)
                    
                    # Method 3: Check if there's a sale price
                    elif 'sale_price' in item and item['sale_price']:
                        price_text = item['sale_price']
                        price = extract_price(price_text)
                    
                    if not price or price == float('inf') or price == 0:
                        print(f"  ✗ Item {idx+1}: No valid price (title: {title[:30]}...)")
                        continue
                    
                    # Get source/merchant
                    source = item.get('source', 'Online Store')
                    
                    # Detect major retailers
                    if 'amazon' in source.lower():
                        source = "Amazon"
                    elif 'flipkart' in source.lower():
                        source = "Flipkart"
                    elif 'myntra' in source.lower():
                        source = "Myntra"
                    elif 'croma' in source.lower():
                        source = "Croma"
                    elif 'reliance' in source.lower():
                        source = "Reliance Digital"
                    
                    # Get product link - Try multiple methods
                    link = None
                    direct_link_attempted = False
                    
                    # Method 1: Try to get direct link via immersive product API
                    if 'serpapi_immersive_product_api' in item:
                        immersive_url = item['serpapi_immersive_product_api']
                        print(f"  🔗 Fetching direct link for item {idx+1}...")
                        direct_link = get_direct_merchant_link(immersive_url, api_key)
                        if direct_link:
                            link = direct_link
                            print(f"  ✅ Got direct merchant link!")
                            direct_link_attempted = True
                    
                    # Method 2: Fallback to product_link (Google Shopping page)
                    if not link:
                        link = item.get('product_link', '')
                        if not direct_link_attempted:
                            print(f"  ⚠️ Using Google Shopping link (no immersive API)")
                    
                    if not link or not link.startswith('http'):
                        print(f"  ✗ Item {idx+1}: No valid link")
                        continue
                    
                    # Get rating if available
                    rating = item.get('rating', 0)
                    reviews = item.get('reviews', 0)
                    
                    # Get delivery info if available
                    delivery = item.get('delivery', 'Standard Delivery')
                    
                    products.append({
                        "site": source,
                        "title": title,
                        "price": price,
                        "price_text": f"₹{int(price):,}",
                        "link": link,
                        "rating": rating,
                        "reviews": reviews,
                        "delivery": delivery
                    })
                    
                    print(f"  ✓ Item {idx+1}: {title[:50]}... - ₹{int(price):,} ({source})")
                    
                except Exception as e:
                    print(f"  ✗ Error parsing item {idx+1}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # Also check 'inline_shopping_results' if shopping_results is empty
        elif 'inline_shopping_results' in data and len(data['inline_shopping_results']) > 0:
            print(f"Found {len(data['inline_shopping_results'])} inline products")
            
            for idx, item in enumerate(data['inline_shopping_results'][:20]):
                try:
                    title = item.get('title', '')
                    if not title or len(title) < 5:
                        continue
                    
                    price_text = item.get('extracted_price') or item.get('price')
                    if not price_text:
                        continue
                    
                    if isinstance(price_text, (int, float)):
                        price = float(price_text)
                    else:
                        price = extract_price(price_text)
                    
                    if price == float('inf') or price == 0:
                        continue
                    
                    source = item.get('source', 'Online Store')
                    link = item.get('link', '')
                    
                    if not link or not link.startswith('http'):
                        continue
                    
                    products.append({
                        "site": source,
                        "title": title,
                        "price": price,
                        "price_text": f"₹{int(price):,}",
                        "link": link,
                        "rating": item.get('rating', 0),
                        "reviews": item.get('reviews', 0)
                    })
                    
                    print(f"  ✓ Item {idx+1}: {title[:50]}... - ₹{int(price):,} ({source})")
                    
                except Exception as e:
                    print(f"  ✗ Error parsing item {idx+1}: {e}")
                    continue
        
        if not products:
            print("⚠️ No products found in API response")
            available_keys = list(data.keys())
            print(f"Available keys in response: {available_keys}")
            
            # Print first few items from response for debugging
            if 'shopping_results' in data:
                print(f"shopping_results exists but empty or unparseable")
            if 'inline_shopping_results' in data:
                print(f"inline_shopping_results exists but empty or unparseable")
            
            # Try to provide helpful message
            return {
                "status": "error", 
                "message": f"No products found for '{product_query}'. Try searching for just the product name (e.g., 'laptop' or 'gaming laptop')",
                "suggestion": "Try simpler search terms like: 'laptop', 'iPhone', 'headphones', etc."
            }
        
        # Sort by price - cheapest first
        products.sort(key=lambda x: x['price'])
        
        print(f"\n✅ Found {len(products)} valid products")
        print(f"🎯 BEST DEAL: {products[0]['title'][:50]}... - {products[0]['price_text']} ({products[0]['site']})")
        
        # Create summary message
        top_3_summary = "\n".join([
            f"{i+1}. {p['title'][:60]} - {p['price_text']} ({p['site']})"
            for i, p in enumerate(products[:3])
        ])
        
        return {
            "status": "success",
            "best_deal": products[0],
            "top_products": products[:5],
            "total_products": len(products),
            "message": f"🎉 Found {len(products)} products!\n\n🏆 TOP 3 DEALS:\n{top_3_summary}",
            "query": product_query
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
