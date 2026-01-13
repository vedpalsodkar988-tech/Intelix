# ability4_brain.py
# Simple local "brain" that picks an ability based on keywords.
# No API key, no internet, no Gemini. Just rules.

def think_and_plan(task: str):
    """
    Decide which ability to use based on the user's task text.
    Always returns a dict like: {"ability": "abilityX"}
    """

    if not task:
        return {"ability": None}

    t = task.lower().strip()

    # ---- Ability 13: internship search (CHECK FIRST - before shopping!) ----
    if "internship" in t or "intern" in t or "internshala" in t:
        return {"ability": "internship"}
    
    # ---- Ability 12: job search (CHECK SECOND - before shopping!) ----
    if "job" in t or "career" in t or "naukri" in t or "indeed" in t or "linkedin jobs" in t:
        # Make sure it's not internship
        if "internship" not in t and "intern" not in t:
            return {"ability": "ability12"}

    # ---- Ability 9: TEXT EXTRACTION (CHECK EARLY!) ----
    # Patterns: "extract text about X from Y", "get info about X from Y", "summarize X from Y"
    extraction_keywords = ["extract", "summarize", "summary", "get info", "get information", "find info"]
    source_keywords = ["from", "on", "at"]
    
    has_extraction = any(keyword in t for keyword in extraction_keywords)
    has_source = any(keyword in t for keyword in source_keywords)
    
    # If it looks like extraction request (even without URL)
    if has_extraction and has_source:
        return {"ability": "ability9"}
    
    # Also catch if they mention extraction with URL
    if has_extraction and ("http" in t or "www" in t or ".com" in t or ".in" in t):
        return {"ability": "ability9"}

    # ---- Shopping Assistant: ANY product search/buy ----
    shopping_actions = ["find", "buy", "order", "purchase", "get", "shop", "looking for", "search for", "want"]
    
    # If ANY shopping action word is present, use shopping
    if any(action in t for action in shopping_actions):
        # Make sure it's not a job/internship search
        if not any(word in t for word in ["job", "career", "position", "employment", "internship", "intern"]):
            # Make sure it's not a research/extraction query
            if not any(word in t for word in ["research about", "information about", "tell me about", "extract", "from bbc", "from techcrunch"]):
                return {"ability": "shopping"}

    # ---- Ability 6: form filling ----
    if "fill" in t and "form" in t:
        return {"ability": "ability6"}

    # ---- Ability 7: universal form filling ----
    if "form" in t and ("http" in t or "www" in t):
        return {"ability": "ability7"}

    # ---- Ability 10: research ----
    if "research" in t or "find information" in t or "tell me about" in t:
        return {"ability": "ability10"}

    # ---- Ability 3: find/extract elements / headlines / titles ----
    if "headline" in t or "headlines" in t or "title" in t or "titles" in t:
        return {"ability": "ability3"}

    # ---- Ability 5: smart browser open / search pages ----
    if "open" in t or "browse" in t or "scroll" in t or "go to" in t or "navigate" in t:
        return {"ability": "ability5"}

    # ---- Ability 2: click + type basic search ----
    if "google" in t or "news" in t:
        return {"ability": "ability2"}

    # Default: if nothing matched, use ability2
    return {"ability": "ability2"}


# Small helper for app.py if needed in future
def think_and_plan_safe(task: str):
    """
    Same as think_and_plan, but guaranteed to never crash.
    """
    try:
        return think_and_plan(task)
    except Exception:
        return {"ability": "ability2"}  # Default to search