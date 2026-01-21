from typing import Dict, Any, List, Optional

# Attribute keywords for entity-level queries
ATTRIBUTE_KEYWORDS = {
    "rating": ["rating", "stars", "star"],
    "address": ["address", "where"],
    "phone": ["phone", "contact", "number"],
    "amenities": ["amenities", "facilities", "features"],
    "parking": ["parking"],
    "pet_friendly": ["pet", "pets", "pet-friendly"],
    "price": ["price", "cost", "tariff", "rate", "rates"],
    "map": ["map", "directions", "location"],
    "vendor_name":["vendor_name", "vendor", "vendor name", "vendor's name", "vendor's name"],
    "wifi": ["wifi", "wi-fi", "internet"],
    "pool": ["pool", "swimming"],
    "bonfire": ["bonfire"],
    "google_location": ["google_location"],
    "website": ["website", "site", "url"],
    "kitchen_available": ["kitchen"],
    "food_available": ["food"],
    "taxes_included": ["tax", "taxes", "tax included"],
    "price_unit": ["price_unit", "unit"],
    "cancellation": ["cancellation", "cancel"],
    "air_conditioned": ["ac", "air conditioned", "air-conditioning", "air conditioning"]

}


def detect_attribute(query: str) -> Optional[str]:
    """
    Detect which attribute is being requested from the query.
    Returns the attribute key or None if no attribute detected.
    """
    q = query.lower()
    
    for attribute, keywords in ATTRIBUTE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in q:
                return attribute
    
    return None


def extract_intent(query: str) -> Dict[str, Any]:
    q = query.lower()

    intent = {
        "category": "hotel",
        "type": "generic_search",   # generic_search | filtered_search | entity_lookup
        "keywords": [],
        "must_have": [],
    }

    # ---- category detection ----
    if "villa" in q:
        intent["category"] = "villa"

    # ---- filters ----
    if "pool" in q:
        intent["type"] = "filtered_search"
        intent["must_have"].append("pool")

    if "family" in q:
        intent["must_have"].append("family")

    if "couple" in q:
        intent["must_have"].append("couple")

    if "luxury" in q:
        intent["must_have"].append("luxury")

    if "budget" in q or "cheap" in q:
        intent["must_have"].append("budget")

    # ---- entity lookup ----
    # Token-based entity name extraction (avoids string corruption)
    STOPWORDS = {
        "what", "is", "the", "of", "tell", "me", "about",
        "rating", "price", "address", "amenities", "phone",
        "location", "where", "map", "directions",
        "hotel", "does", "do", "have", "has", "a", "an",
        "what's", "show", "find", "something",
        "wifi", "wi-fi", "internet", "pool", "swimming", "bonfire",
        "website", "site", "url", "kitchen", "food",
        "tax", "taxes", "cancellation", "cancel", "unit"
    }
    
    # Detect entity lookup patterns
    entity_patterns = [
        "tell me about",
        "tell me something about",
        "what is",
        "what's",
        "show me",
        "find",
    ]
    
    # Check if query matches entity lookup pattern
    is_entity_query = False
    for pattern in entity_patterns:
        if pattern in q:
            is_entity_query = True
            break
    
    # Also check for direct hotel mentions or attribute queries
    if not is_entity_query:
        # Check if query contains hotel + attribute keywords
        has_hotel = "hotel" in q
        has_attribute = detect_attribute(query) is not None
        if has_hotel and has_attribute:
            is_entity_query = True
    
    # Extract entity name using token-based parsing
    extracted_entity_name = None
    if is_entity_query:
        tokens = q.split()
        entity_tokens = [t for t in tokens if t not in STOPWORDS]
        
        if entity_tokens:
            intent["type"] = "entity_lookup"
            extracted_entity_name = " ".join(entity_tokens)
            intent["entity_name"] = extracted_entity_name

    # ---- FINAL OVERRIDE: Force entity_lookup if attribute + entity detected ----
    # This ensures entity + attribute queries ALWAYS trigger bypass logic
    detected_attr = detect_attribute(query)
    if detected_attr is not None:
        # If entity name was already extracted, use it
        if extracted_entity_name:
            intent["type"] = "entity_lookup"
            intent["entity_name"] = extracted_entity_name
        else:
            # Try to extract entity name if not already done
            tokens = q.split()
            entity_tokens = [t for t in tokens if t not in STOPWORDS]
            if entity_tokens:
                intent["type"] = "entity_lookup"
                intent["entity_name"] = " ".join(entity_tokens)

    intent["keywords"] = intent["must_have"]
    return intent
