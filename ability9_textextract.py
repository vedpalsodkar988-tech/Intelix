import re
import urllib.request
from urllib.error import URLError, HTTPError
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyC5Lm40-n4EBnNOghBZEU9e60-glIijKuE")

# Try the exact model string from official docs
model = genai.GenerativeModel('gemini-1.5-flash')


def parse_extraction_request(task):
    """
    Parse user request to extract topic and website
    Examples:
    - "extract text about AI from BBC"
    - "get info about climate change from TechCrunch"
    - "summarize Apple products from CNET"
    """
    task_lower = task.lower()
    
    # Extract website
    website_patterns = [
        r'from\s+([\w\-]+\.[\w]+)',  # "from bbc.com"
        r'from\s+([\w\-]+)',  # "from bbc"
        r'on\s+([\w\-]+\.[\w]+)',  # "on techcrunch.com"
        r'on\s+([\w\-]+)',  # "on techcrunch"
    ]
    
    website = None
    for pattern in website_patterns:
        match = re.search(pattern, task_lower)
        if match:
            website = match.group(1)
            if '.' not in website:
                # Add .com if no extension
                website = website + '.com'
            break
    
    # Extract topic
    topic_patterns = [
        r'about\s+(.+?)\s+(?:from|on)',  # "about AI from"
        r'(?:extract|get|find|summarize)\s+(?:text|info|information)?\s*(?:about|on)?\s+(.+?)\s+(?:from|on)',
    ]
    
    topic = None
    for pattern in topic_patterns:
        match = re.search(pattern, task_lower)
        if match:
            topic = match.group(1).strip()
            break
    
    # Fallback: if no topic found, try to extract main subject
    if not topic:
        # Remove command words to find topic
        clean = re.sub(r'\b(extract|get|find|summarize|text|info|information|from|on|about)\b', '', task_lower)
        if website:
            clean = clean.replace(website, '')
        topic = clean.strip()
    
    return topic, website


def search_website_for_topic(website, topic):
    """
    Search the website for specific topic
    Returns URL of search results or main page
    """
    # Common search URL patterns
    search_patterns = {
        'bbc': f'https://www.bbc.com/search?q={topic.replace(" ", "+")}',
        'techcrunch': f'https://techcrunch.com/?s={topic.replace(" ", "+")}',
        'cnet': f'https://www.cnet.com/search/?q={topic.replace(" ", "+")}',
        'forbes': f'https://www.forbes.com/search/?q={topic.replace(" ", "+")}',
        'reuters': f'https://www.reuters.com/site-search/?query={topic.replace(" ", "+")}',
        'default': f'https://www.{website}/search?q={topic.replace(" ", "+")}'
    }
    
    # Extract base domain name
    base_domain = website.replace('.com', '').replace('.in', '').replace('.org', '')
    
    if base_domain in search_patterns:
        return search_patterns[base_domain]
    else:
        # Try generic search or just go to homepage
        if not website.startswith('http'):
            website = 'https://' + website
        return website


def extract_and_summarize(task):
    """
    Extract text about a specific topic from a website
    NO BROWSER OPENING - Returns text summary only
    """
    print(f"🔍 Processing: {task}")
    
    result = {
        "status": "error",
        "summary": "",
        "keywords": [],
        "topic": "",
        "website": "",
        "error": ""
    }

    # Parse the request
    topic, website = parse_extraction_request(task)
    
    if not topic or not website:
        result["error"] = """❌ Could not understand request. Please use format:
        
Examples:
• "extract text about AI from BBC"
• "get info about climate change from TechCrunch"
• "summarize Apple products from CNET"
"""
        return result

    result["topic"] = topic
    result["website"] = website
    
    print(f"✓ Topic: {topic}")
    print(f"✓ Website: {website}")

    # Get URL to fetch
    url = search_website_for_topic(website, topic)
    print(f"✓ Fetching: {url}")

    # Fetch webpage content (NO BROWSER - just HTTP request)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            webpage = response.read().decode("utf-8", "ignore")
        print(f"✓ Fetched {len(webpage)} chars")
    except Exception as e:
        result["error"] = f"❌ Could not fetch from {website}: {str(e)}"
        return result

    # Clean HTML and extract text
    text = re.sub(r"<script.*?</script>", "", webpage, flags=re.DOTALL)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text[:15000]
    
    if len(text.strip()) < 100:
        result["error"] = f"❌ Could not extract meaningful content from {website}"
        return result
    
    print(f"✓ Cleaned text: {len(text)} chars")

    # AI: Extract info about specific topic and create bullet summary
    prompt = f"""You are extracting information about "{topic}" from {website}.

Analyze this webpage content and extract ONLY information related to "{topic}".

Create a summary with:
1. 5-7 bullet points about "{topic}" (most important facts/info only)
2. 3-5 key keywords related to "{topic}"

Rules:
- Focus ONLY on "{topic}" - ignore unrelated content
- Each bullet should be clear and concise (1-2 sentences)
- Start bullets with •
- Extract facts, not opinions

Content from {website}:
{text}

Respond in this format:
TOPIC: {topic}

KEY POINTS:
• [specific point about {topic}]
• [another point about {topic}]
• [another point]
...

KEYWORDS: [keyword1, keyword2, keyword3]
"""

    try:
        print("⏳ AI analyzing content...")
        response = model.generate_content(prompt)
        ai_output = response.text.strip()
        
        # Parse response
        if "KEY POINTS:" in ai_output:
            parts = ai_output.split("KEYWORDS:")
            summary_part = parts[0].replace("TOPIC:", "").replace(f"{topic}", "").replace("KEY POINTS:", "").strip()
            
            result["status"] = "success"
            result["summary"] = summary_part
            
            if len(parts) > 1:
                keywords_part = parts[1].strip()
                result["keywords"] = [k.strip() for k in keywords_part.split(",") if k.strip()]
            
            print("✅ Summary created!")
        else:
            result["status"] = "success"
            result["summary"] = ai_output
            
    except Exception as e:
        result["error"] = f"❌ AI analysis failed: {str(e)}"
        return result

    return result


# For testing
if __name__ == "__main__":
    test_tasks = [
        "extract text about AI from BBC",
        "get info about climate change from TechCrunch",
        "summarize Apple products from CNET"
    ]
    
    for task in test_tasks:
        print("\n" + "="*60)
        result = extract_and_summarize(task)
        print(f"\nTASK: {task}")
        print(f"STATUS: {result['status']}")
        if result['status'] == 'success':
            print(f"\nTOPIC: {result['topic']}")
            print(f"FROM: {result['website']}")
            print(f"\nSUMMARY:\n{result['summary']}")
            print(f"\nKEYWORDS: {', '.join(result['keywords'])}")
        else:
            print(f"ERROR: {result['error']}")