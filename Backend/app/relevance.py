# Import re for text normalization and token extraction
import re


# Normalize text so comparisons are case-insensitive and spacing is consistent
def normalize_text(text: str) -> str:
    # Lowercase the text, collapse repeated whitespace, and trim outer spaces
    return re.sub(r"\s+", " ", text.lower()).strip()


# Extract useful query terms while ignoring very common filler words
def extract_query_terms(query: str) -> list[str]:
    # Split the query into alphanumeric words
    words = re.findall(r"[a-zA-Z0-9]+", query.lower())

    # Ignore very common words that usually do not help retrieval quality
    stopwords = {
        "what", "is", "are", "the", "a", "an", "of", "in", "on", "for",
        "to", "and", "or", "does", "do", "how", "why", "when", "where",
        "explain", "define", "describe", "tell", "me", "about"
    }

    # Return only the more meaningful terms
    return [word for word in words if word not in stopwords]


# Convert text into a set of whole-word tokens for stricter lexical matching
def extract_text_terms(text: str) -> set[str]:
    # Normalize and tokenize the text into full words only
    return set(re.findall(r"[a-zA-Z0-9]+", normalize_text(text)))


# Check whether the chunk text has enough meaningful lexical overlap with the query
def has_reasonable_keyword_overlap(query: str, chunk_text: str) -> bool:
    # Extract important query terms
    query_terms = extract_query_terms(query)

    # If the query has no meaningful terms, do not reject based on overlap
    if not query_terms:
        return True

    # Extract full-word tokens from the chunk text
    text_terms = extract_text_terms(chunk_text)

    # Count how many query terms appear as full words in the chunk
    hits = sum(1 for term in query_terms if term in text_terms)

    # For short queries with only one useful term, require that term to appear exactly
    if len(query_terms) == 1:
        return hits == 1

    # For slightly longer queries, require at least half of the useful terms to match
    required_hits = max(1, len(query_terms) // 2)
    return hits >= required_hits


# Check whether the top reranked chunk is strong enough to trust
def is_strong_match(best_chunk: dict, min_score: float = 0.60) -> bool:
    # Read the reranked score safely and compare it to a stricter threshold
    return float(best_chunk.get("rerank_score", 0.0)) >= min_score