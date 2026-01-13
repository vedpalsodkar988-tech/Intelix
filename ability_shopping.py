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


def save_cookies(context, site_name):
    """Save browser cookies for auto-login"""
    try:
        cookies = context.cookies()
        cookies_dir = "browser_cookies"
        os.makedirs(cookies_dir, exist_ok=True)
        
        with open(f"{cookies_dir}/{site_name}_cookies.json", "w") as f:
            json.dump(cookies, f)
        print(f"✅ Saved {site_name} login cookies")
    except Exception as e:
        print(f"⚠️ Could not save cookies: {e}")


def load_cookies(context, site_name):
    """Load saved cookies for auto-login"""
    try:
        cookies_file = f"browser_cookies/{site_name}_cookies.json"
        if os.path.exists(cookies_file):
            with open(cookies_file, "r") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
            print(f"✅ Loaded {site_name} login cookies")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Could not load cookies: {e}")
        return False


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
        page.goto("https://www.amazon.in", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(2000)
        
        # Search
        search_box = page.locator("#twotabsearchtextbox")
        search_box.fill(query, timeout=5000)
        search_box.press("Enter")
        page.wait_for_timeout(3000)
        
        print(f"✓ Amazon search completed for: {query}")
        
        products = []
        page.wait_for_selector("[data-component-type='s-search-result']", timeout=10000)
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
    """Search Flipkart with Playwright - UPDATED SELECTORS"""
    print("🔍 Searching Flipkart...")
    
    try:
        page.goto("https://www.flipkart.com", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(2000)
        
        # Close login popup if appears
        try:
            page.locator("button._2KpZ6l._2doB4z").click(timeout=2000)
        except:
            pass
        
        search_box = page.locator("input[name='q']")
        search_box.fill(query, timeout=5000)
        search_box.press("Enter")
        page.wait_for_timeout(3000)
        
        print(f"✓ Flipkart search completed for: {query}")
        
        products = []
        
        # Wait for results - try multiple selectors
        try:
            page.wait_for_selector("div[data-id]", timeout=10000)
        except:
            try:
                page.wait_for_selector("div._75nlfW", timeout=5000)
            except:
                print("⚠️ Could not find Flipkart results container")
                return []
        
        # Get all product items
        items = page.locator("div[data-id]").all()[:5]
        print(f"Found {len(items)} items on Flipkart")
        
        for idx, item in enumerate(items):
            try:
                # EXTRACT TITLE - Multiple methods
                title = None
                title_selectors = [
                    ".KzDlHZ",           # Common product title class
                    ".wjcEIp",           # Alternative title class
                    ".IRpwTa",           # Another title class
                    "a.wjcEIp",          # Title in link
                    "a.VJA3rP",          # New title class
                    "div.KzDlHZ",        # Div wrapped title
                    "a[title]"           # Any link with title attribute
                ]
                
                for selector in title_selectors:
                    try:
                        title_elem = item.locator(selector).first
                        if title_elem.count() > 0:
                            title = title_elem.inner_text(timeout=2000)
                            if title and len(title) > 5:
                                break
                            # Try getting title attribute if inner_text fails
                            title = title_elem.get_attribute("title", timeout=2000)
                            if title and len(title) > 5:
                                break
                    except:
                        continue
                
                if not title or len(title) < 5:
                    print(f"⚠️ Item {idx+1}: No title found, skipping")
                    continue
                
                # EXTRACT PRICE - Multiple methods with logging
                price_text = None
                price_selectors = [
                    "._30jeq3",          # Old price class
                    ".Nx9bqj",           # Alternative price class  
                    "._4b5DiR",          # New price class
                    ".hl05eU",           # Another price class
                    "div._30jeq3",       # Div wrapped price
                    "div.Nx9bqj",        # Div alternative
                    "div._25b18c",       # Newer price class
                    "[class*='price']"   # Any class containing 'price'
                ]
                
                for selector in price_selectors:
                    try:
                        price_elem = item.locator(selector).first
                        if price_elem.count() > 0:
                            price_text = price_elem.inner_text(timeout=2000)
                            if price_text and any(char.isdigit() for char in price_text):
                                print(f"  💰 Found price with selector '{selector}': {price_text}")
                                break
                    except:
                        continue
                
                if not price_text:
                    print(f"⚠️ Item {idx+1}: No price found for '{title[:30]}...', skipping")
                    continue
                
                price = extract_price(price_text)
                if price == float('inf'):
                    print(f"⚠️ Item {idx+1}: Could not parse price '{price_text}', skipping")
                    continue
                
                # EXTRACT LINK
                link = None
                try:
                    link = item.locator("a").first.get_attribute("href", timeout=3000)
                except:
                    print(f"⚠️ Item {idx+1}: No link found, skipping")
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
                print(f"✗ Item {idx+1}: Error - {e}")
                continue
        
        print(f"✅ Flipkart: Found {len(products)} products")
        return products
    
    except Exception as e:
        print(f"❌ Flipkart error: {e}")
        import traceback
        traceback.print_exc()
        return []


def shopping_assistant_task(query, user_profile=None):
    """AI Shopping Assistant with Playwright"""
    print("🛒 AI Shopping Assistant Starting (Playwright)...")
    print(f"Query: {query}")
    
    # Detect website preference FIRST
    website_preference = detect_website_preference(query)
    
    product_query = re.sub(r'\b(find|search|buy|order|get|purchase|amazon|flipkart|on|from|at|in)\b', ' ', query.lower()).strip()
    product_query = re.sub(r'\s+', ' ', product_query)  # Remove extra spaces
    print(f"Cleaned query: {product_query}")
    
    with sync_playwright() as p:
        # Use persistent context - keeps login across sessions!
        user_data_dir = "./browser_data"
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=['--start-maximized'],
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            all_products = []
            
            # Search based on user preference
            if website_preference == 'amazon':
                print("\n===== AMAZON ONLY (User Specified) =====")
                amazon_products = search_amazon(page, product_query)
                all_products.extend(amazon_products)
                
            elif website_preference == 'flipkart':
                print("\n===== FLIPKART ONLY (User Specified) =====")
                flipkart_products = search_flipkart(page, product_query)
                all_products.extend(flipkart_products)
                
            else:  # both
                print("\n===== COMPARING BOTH SITES =====")
                # Search Amazon
                print("\n--- AMAZON SEARCH ---")
                amazon_products = search_amazon(page, product_query)
                all_products.extend(amazon_products)
                
                # Search Flipkart
                print("\n--- FLIPKART SEARCH ---")
                flipkart_products = search_flipkart(page, product_query)
                all_products.extend(flipkart_products)
            
            print(f"\n===== TOTAL: {len(all_products)} PRODUCTS =====")
            
            if not all_products:
                context.close()
                return {"status": "error", "message": "No products found"}
            
            # Find best deal - TRULY NEUTRAL
            best_deal = min(all_products, key=lambda x: x['price'])
            
            print(f"\n🎯 BEST DEAL:")
            print(f"Site: {best_deal['site']}")
            print(f"Product: {best_deal['title']}")
            print(f"Price: {best_deal['price_text']}")
            
            # Show comparison if both sites searched
            if website_preference == 'both' and len(all_products) > 1:
                print(f"\n📊 COMPARISON:")
                amazon_items = [p for p in all_products if p['site'] == 'Amazon']
                flipkart_items = [p for p in all_products if p['site'] == 'Flipkart']
                
                if amazon_items:
                    cheapest_amazon = min(amazon_items, key=lambda x: x['price'])
                    print(f"  Amazon cheapest: {cheapest_amazon['price_text']}")
                
                if flipkart_items:
                    cheapest_flipkart = min(flipkart_items, key=lambda x: x['price'])
                    print(f"  Flipkart cheapest: {cheapest_flipkart['price_text']}")
                
                print(f"  ✅ Winner: {best_deal['site']} ({best_deal['price_text']})")
            
            # Open best deal
            page.goto(best_deal['link'], wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
            
            # CENTERED POPUP
            print("\n⚠️ ASKING USER CONFIRMATION...")
            
            product_title = best_deal['title'].replace("'", "\\'").replace('"', '\\"')[:80]
            product_price = best_deal['price_text']
            product_site = best_deal['site']
            
            confirmation_script = f"""
                new Promise((resolve) => {{
                    window.scrollTo(0, 0);
                    document.documentElement.style.overflow = 'hidden';
                    document.body.style.overflow = 'hidden';
                    
                    let overlay = document.createElement('div');
                    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.95);z-index:999999999;display:flex;align-items:center;justify-content:center;';
                    
                    let dialog = document.createElement('div');
                    dialog.style.cssText = 'background:white;border-radius:15px;max-width:450px;width:90%;max-height:80vh;overflow-y:auto;';
                    
                    dialog.innerHTML = `
                        <div style="background:linear-gradient(135deg, #667eea, #764ba2);padding:20px;text-align:center;border-radius:15px 15px 0 0;">
                            <div style="font-size:35px;">🎉</div>
                            <h2 style="color:white;font-size:22px;margin:8px 0;font-weight:bold;">BEST DEAL!</h2>
                        </div>
                        <div style="padding:20px;">
                            <div style="background:#f5f5f5;padding:15px;border-radius:10px;margin-bottom:15px;">
                                <p style="color:#666;font-size:10px;margin:0 0 5px 0;text-transform:uppercase;font-weight:600;">Product</p>
                                <h3 style="color:#333;font-size:14px;margin:0 0 12px 0;line-height:1.3;">{product_title}</h3>
                                <div style="display:flex;justify-content:space-between;border-top:1px solid #ddd;padding-top:10px;">
                                    <div>
                                        <p style="color:#999;font-size:9px;margin:0;text-transform:uppercase;">Price</p>
                                        <p style="color:#667eea;font-size:22px;margin:3px 0;font-weight:bold;">{product_price}</p>
                                    </div>
                                    <div style="text-align:right;">
                                        <p style="color:#999;font-size:9px;margin:0;text-transform:uppercase;">On</p>
                                        <p style="color:#333;font-size:16px;margin:3px 0;font-weight:bold;">{product_site}</p>
                                    </div>
                                </div>
                            </div>
                            <p style="text-align:center;color:#333;font-size:14px;margin:15px 0;font-weight:600;">Ready to buy?</p>
                            <div style="display:flex;gap:10px;">
                                <button id="buyYes" style="flex:1;padding:12px;background:#4CAF50;color:white;border:none;border-radius:8px;font-size:14px;cursor:pointer;font-weight:bold;">✅ YES</button>
                                <button id="buyNo" style="flex:1;padding:12px;background:#f44336;color:white;border:none;border-radius:8px;font-size:14px;cursor:pointer;font-weight:bold;">❌ NO</button>
                            </div>
                        </div>
                    `;
                    
                    overlay.appendChild(dialog);
                    document.body.appendChild(overlay);
                    
                    document.getElementById('buyYes').onclick = () => {{
                        document.documentElement.style.overflow = '';
                        document.body.style.overflow = '';
                        overlay.remove();
                        resolve(true);
                    }};
                    
                    document.getElementById('buyNo').onclick = () => {{
                        document.documentElement.style.overflow = '';
                        document.body.style.overflow = '';
                        overlay.remove();
                        resolve(false);
                    }};
                }})
            """
            
            print("⏳ Waiting for user decision...")
            user_confirmed = page.evaluate(confirmation_script)
            print(f"✓ User response: {user_confirmed}")
            
            if not user_confirmed:
                print("❌ User cancelled")
                context.close()
                return {"status": "cancelled", "message": "User cancelled purchase"}
            
            print("✅ User confirmed! Adding to cart...")
            
            # Add to cart and checkout
            try:
                page.locator("#add-to-cart-button").click(timeout=5000)
                print("✅ Added to cart!")
                page.wait_for_timeout(3000)
                
                # Go to cart
                page.goto(f"https://www.amazon.in/gp/cart/view.html" if best_deal['site'] == "Amazon" else "https://www.flipkart.com/viewcart")
                page.wait_for_timeout(3000)
                
                # Check if logged in
                is_logged_in = False
                try:
                    if best_deal['site'] == "Amazon":
                        is_logged_in = page.locator("#nav-link-accountList").is_visible()
                    else:
                        is_logged_in = page.locator("div._1FXNat").is_visible()
                except:
                    pass
                
                if not is_logged_in:
                    print("⚠️ User not logged in - please login in this window!")
                    page.evaluate(f"alert('Please LOGIN to {best_deal['site']} in this window!\\n\\nYour login will be saved for next time.\\n\\nClick OK after logging in.');")
                    page.wait_for_timeout(90000)  # Wait 90 seconds
                
                print("✓ Login saved! Will be used for next purchase")
                
                # Proceed to checkout
                print("Going to checkout...")
                if best_deal['site'] == "Amazon":
                    page.locator("input[name='proceedToRetailCheckout']").click(timeout=10000)
                else:
                    page.locator("button._2KpZ6l._2U9uOA").click(timeout=10000)
                
                page.wait_for_timeout(5000)
                print("🎉 At checkout! User can complete payment")
                
            except Exception as e:
                print(f"⚠️ Error: {e}")
            
            page.wait_for_timeout(120000)
            context.close()
            
            return {
                "status": "success",
                "best_deal": best_deal,
                "total_products": len(all_products),
                "website_preference": website_preference,
                "message": "Shopping completed!"
            }
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            context.close()
            return {"status": "error", "error": str(e)}