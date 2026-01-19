from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import re


def extract_price(price_text):
    """Extract numeric price from text"""
    if not price_text:
        return float('inf')
    clean = re.sub(r'[₹Rs.,\s]', '', price_text)
    try:
        return float(clean)
    except:
        return float('inf')


def shopping_assistant_task(query, user_profile=None):
    """AI Shopping Assistant using Google Shopping"""
    print("🛒 AI Shopping Assistant Starting (Google Shopping)...")
    print(f"Query: {query}")
    
    # Clean the query
    product_query = re.sub(r'\b(find|search|buy|order|get|purchase|best|top)\b', '', query.lower()).strip()
    product_query = re.sub(r'\s+', ' ', product_query)
    print(f"Cleaned query: {product_query}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path='/usr/bin/chromium',
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-IN',
            timezone_id='Asia/Kolkata'
        )
        
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        
        page = context.new_page()
        
        try:
            # Search Google Shopping
            print("🔍 Searching Google Shopping...")
            search_url = f"https://www.google.com/search?q={product_query}&tbm=shop&hl=en-IN&gl=IN"
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            
            print("✓ Google Shopping loaded")
            
            products = []
            
            # Wait for product results - try multiple selectors
            try:
                page.wait_for_selector("div.sh-dgr__grid-result", timeout=20000)
                items = page.locator("div.sh-dgr__grid-result").all()[:10]
            except:
                try:
                    page.wait_for_selector("div[data-docid]", timeout=10000)
                    items = page.locator("div[data-docid]").all()[:10]
                except:
                    try:
                        page.wait_for_selector(".sh-dlr__list-result", timeout=10000)
                        items = page.locator(".sh-dlr__list-result").all()[:10]
                    except:
                        print("⚠️ No results container found")
                        browser.close()
                        return {"status": "error", "message": "No products found"}
            print(f"Found {len(items)} product listings")
            
            for idx, item in enumerate(items):
                try:
                    # Extract title - multiple selectors
                    title = None
                    title_selectors = ["h3", "h4", ".tAxDx", "span[role='heading']", ".Xjkr3b", "a"]
                    for sel in title_selectors:
                        try:
                            elem = item.locator(sel).first
                            if elem.count() > 0:
                                title = elem.inner_text(timeout=2000)
                                if title and len(title) > 5:
                                    break
                        except:
                            continue
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # Extract price - multiple selectors
                    price_text = None
                    price_selectors = ["span.a8Pemb", "div.a8Pemb", ".T14wmb", "span[aria-label*='₹']", "b"]
                    for sel in price_selectors:
                        try:
                            elem = item.locator(sel).first
                            if elem.count() > 0:
                                price_text = elem.inner_text(timeout=2000)
                                if price_text and any(char.isdigit() for char in price_text):
                                    break
                        except:
                            continue
                    
                    price = extract_price(price_text)
                    if price == float('inf') or price == 0:
                        continue
                    
                    # Extract merchant/site
                    site = "Online Store"
                    try:
                        site_elem = item.locator("div.aULzUe").first.inner_text(timeout=2000)
                        if site_elem:
                            site = site_elem
                            # Detect if Amazon or Flipkart
                            if 'amazon' in site.lower():
                                site = "Amazon"
                            elif 'flipkart' in site.lower():
                                site = "Flipkart"
                    except:
                        pass
                    
                    # Extract link
                    link = None
                    try:
                        link_elem = item.locator("a").first
                        link = link_elem.get_attribute("href", timeout=3000)
                    except:
                        continue
                    
                    if not link:
                        continue
                    
                    # Convert Google Shopping redirect to actual link
                    if link.startswith("/url?"):
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                        if 'url' in parsed:
                            link = parsed['url'][0]
                    
                    if not link.startswith('http'):
                        link = f"https://www.google.com{link}"
                    
                    products.append({
                        "site": site,
                        "title": title,
                        "price": price,
                        "price_text": f"₹{int(price):,}",
                        "link": link
                    })
                    
                    print(f"✓ Item {idx+1}: {title[:50]}... - ₹{int(price):,} ({site})")
                    
                except Exception as e:
                    print(f"✗ Error on item {idx+1}: {e}")
                    continue
            
            browser.close()
            
            if not products:
                return {"status": "error", "message": "No products found"}
            
            # Sort by price
            products.sort(key=lambda x: x['price'])
            
            print(f"\n✅ Found {len(products)} products")
            print(f"🎯 BEST DEAL: {products[0]['title'][:50]}... - {products[0]['price_text']} ({products[0]['site']})")
            
            return {
                "status": "success",
                "best_deal": products[0],
                "top_products": products[:3],
                "total_products": len(products),
                "message": "Shopping completed!"
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            browser.close()
            return {"status": "error", "error": str(e)}
