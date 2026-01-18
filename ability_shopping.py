from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import time
import re
import json
import os


def extract_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return float('inf')
    clean = re.sub(r'[₹Rs.,\s]', '', price_text)
    try:
        return float(clean)
    except:
        return float('inf')


def detect_website_preference(query):
    """
    Detect if user specified a particular website
    Returns: 'amazon', 'flipkart', or 'both'
    """
    query_lower = query.lower()
    
    # Check for explicit mentions
    has_amazon = any(word in query_lower for word in ['amazon', 'amzn', 'amazon.in'])
    has_flipkart = any(word in query_lower for word in ['flipkart', 'flipkart.com', 'fk'])
    
    if has_amazon and not has_flipkart:
        print("🎯 User specified: Amazon only")
        return 'amazon'
    elif has_flipkart and not has_amazon:
        print("🎯 User specified: Flipkart only")
        return 'flipkart'
    else:
        print("🎯 No preference - will compare both sites")
        return 'both'


def search_amazon(page, query):
    """Search Amazon with Playwright"""
    print("🔍 Searching Amazon...")
    
    try:
        page.goto("https://www.amazon.in", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        
        # Search
        search_box = page.locator("#twotabsearchtextbox")
        search_box.fill(query, timeout=10000)
        search_box.press("Enter")
        page.wait_for_timeout(5000)
        
        print(f"✓ Amazon search completed for: {query}")
        
        products = []
        page.wait_for_selector("[data-component-type='s-search-result']", timeout=30000)
        items = page.locator("[data-component-type='s-search-result']").all()[:5]
        print(f"Found {len(items)} items on Amazon")
        
        for idx, item in enumerate(items):
            try:
                title = None
                try:
                    title = item.locator("h2").inner_text(timeout=3000)
                except:
                    try:
                        title = item.locator(".a-text-normal").inner_text(timeout=3000)
                    except:
                        continue
                
                if not title or len(title) < 5:
                    continue
                
                price_text = None
                try:
                    price_text = item.locator(".a-price-whole").first.inner_text(timeout=3000)
                except:
                    try:
                        price_text = item.locator(".a-price").first.inner_text(timeout=3000)
                    except:
                        continue
                
                price = extract_price(price_text)
                if price == float('inf'):
                    continue
                
                try:
                    link = item.locator("h2 a").first.get_attribute("href", timeout=3000)
                except:
                    try:
                        link = item.locator("a").first.get_attribute("href", timeout=3000)
                    except:
                        continue
                
                full_link = f"https://www.amazon.in{link}" if link.startswith("/") else link
                
                products.append({
                    "site": "Amazon",
                    "title": title,
                    "price": price,
                    "price_text": f"₹{int(price):,}",
                    "link": full_link
                })
                
                print(f"✓ Item {idx+1}: {title[:40]}... - ₹{int(price):,}")
            except Exception as e:
                print(f"✗ Skipping item {idx+1}")
                continue
        
        print(f"✅ Amazon: Found {len(products)} products")
        return products
    
    except Exception as e:
        print(f"❌ Amazon error: {e}")
        return []


def search_flipkart(page, query):
    """Search Flipkart with Playwright"""
    print("🔍 Searching Flipkart...")
    
    try:
        page.goto("https://www.flipkart.com", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        
        # Close login popup if appears
        try:
            page.locator("button._2KpZ6l._2doB4z").click(timeout=3000)
        except:
            pass
        
        search_box = page.locator("input[name='q']")
        search_box.fill(query, timeout=10000)
        search_box.press("Enter")
        page.wait_for_timeout(5000)
        
        print(f"✓ Flipkart search completed for: {query}")
        
        products = []
        
        try:
            page.wait_for_selector("div[data-id]", timeout=30000)
        except:
            try:
                page.wait_for_selector("div._75nlfW", timeout=10000)
            except:
                print("⚠️ Could not find Flipkart results container")
                return []
        
        items = page.locator("div[data-id]").all()[:5]
        print(f"Found {len(items)} items on Flipkart")
        
        for idx, item in enumerate(items):
            try:
                title = None
                title_selectors = [".KzDlHZ", ".wjcEIp", ".IRpwTa", "a.wjcEIp", "a.VJA3rP", "div.KzDlHZ", "a[title]"]
                
                for selector in title_selectors:
                    try:
                        title_elem = item.locator(selector).first
                        if title_elem.count() > 0:
                            title = title_elem.inner_text(timeout=2000)
                            if title and len(title) > 5:
                                break
                            title = title_elem.get_attribute("title", timeout=2000)
                            if title and len(title) > 5:
                                break
                    except:
                        continue
                
                if not title or len(title) < 5:
                    continue
                
                price_text = None
                price_selectors = ["._30jeq3", ".Nx9bqj", "._4b5DiR", ".hl05eU", "div._30jeq3", "div.Nx9bqj", "div._25b18c", "[class*='price']"]
                
                for selector in price_selectors:
                    try:
                        price_elem = item.locator(selector).first
                        if price_elem.count() > 0:
                            price_text = price_elem.inner_text(timeout=2000)
                            if price_text and any(char.isdigit() for char in price_text):
                                break
                    except:
                        continue
                
                if not price_text:
                    continue
                
                price = extract_price(price_text)
                if price == float('inf'):
                    continue
                
                try:
                    link = item.locator("a").first.get_attribute("href", timeout=3000)
                except:
                    continue
                
                full_link = f"https://www.flipkart.com{link}" if link.startswith("/") else link
                
                products.append({
                    "site": "Flipkart",
                    "title": title,
                    "price": price,
                    "price_text": f"₹{int(price):,}",
                    "link": full_link
                })
                
                print(f"✓ Item {idx+1}: {title[:40]}... - ₹{int(price):,}")
                
            except Exception as e:
                continue
        
        print(f"✅ Flipkart: Found {len(products)} products")
        return products
    
    except Exception as e:
        print(f"❌ Flipkart error: {e}")
        return []


def shopping_assistant_task(query, user_profile=None):
    """AI Shopping Assistant with Playwright"""
    print("🛒 AI Shopping Assistant Starting (Playwright)...")
    print(f"Query: {query}")
    
    website_preference = detect_website_preference(query)
    
    product_query = re.sub(r'\b(find|search|buy|order|get|purchase|amazon|flipkart|on|from|at|in)\b', ' ', query.lower()).strip()
    product_query = re.sub(r'\s+', ' ', product_query)
    print(f"Cleaned query: {product_query}")
    
    with sync_playwright() as p:
        # Use system Chromium for Render
        browser = p.chromium.launch(
            headless=True,
            executable_path='/usr/bin/chromium',
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            all_products = []
            
            if website_preference == 'amazon':
                amazon_products = search_amazon(page, product_query)
                all_products.extend(amazon_products)
                
            elif website_preference == 'flipkart':
                flipkart_products = search_flipkart(page, product_query)
                all_products.extend(flipkart_products)
                
            else:
                amazon_products = search_amazon(page, product_query)
                all_products.extend(amazon_products)
                
                flipkart_products = search_flipkart(page, product_query)
                all_products.extend(flipkart_products)
            
            print(f"\n===== TOTAL: {len(all_products)} PRODUCTS =====")
            
            if not all_products:
                browser.close()
                return {"status": "error", "message": "No products found"}
            
            # Sort by price - best deals first
            all_products.sort(key=lambda x: x['price'])
            best_deal = all_products[0]
            
            print(f"\n🎯 BEST DEAL:")
            print(f"Site: {best_deal['site']}")
            print(f"Product: {best_deal['title']}")
            print(f"Price: {best_deal['price_text']}")
            
            browser.close()
            
            return {
                "status": "success",
                "best_deal": best_deal,
                "top_products": all_products[:3],
                "total_products": len(all_products),
                "website_preference": website_preference,
                "message": "Shopping completed!"
            }
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            browser.close()
            return {"status": "error", "error": str(e)}

