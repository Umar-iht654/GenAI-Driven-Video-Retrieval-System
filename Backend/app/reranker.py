# Import regular expressions for lightweight text cleaning and pattern matching
import re


# Normalize text so matching is case-insensitive and whitespace is consistent
def normalize_text(text: str) -> str:
    # Lowercase the text, collapse repeated whitespace, and trim outer spaces
    return re.sub(r"\s+", " ", text.lower()).strip()


# Extract useful query words while removing very common filler words
def extract_query_terms(query: str) -> list[str]:
    # Split the query into alphanumeric tokens
    words = re.findall(r"[a-zA-Z0-9]+", query.lower())

    # Ignore common words that usually do not help retrieval much
    stopwords = {
        "what", "is", "are", "the", "a", "an", "of", "in", "on", "for",
        "to", "and", "or", "does", "do", "how", "why", "when", "where",
        "explain", "define", "describe", "tell", "me", "about"
    }

    # Return only the more meaningful terms
    return [word for word in words if word not in stopwords]


# Detect broad query intent so we can apply small generic reranking preferences
def detect_query_intent(query: str) -> str:
    # Normalize the question for easier matching
    normalized_query = normalize_text(query)

    # Treat these as definition-style questions
    if re.match(r"^(what is|what are|who is|define|definition of|meaning of)\b", normalized_query):
        return "definition"

    # Treat these as explanation-style questions
    if re.match(r"^(explain|describe|how does|how do|why does|why do)\b", normalized_query):
        return "explanation"

    # Otherwise treat the question as a general retrieval query
    return "general"


# Measure simple lexical overlap between the query and a chunk
def compute_keyword_overlap_score(query_terms: list[str], chunk_text: str) -> float:
    # If there are no useful query terms, return no lexical boost
    if not query_terms:
        return 0.0

    # Normalize the chunk text for consistent matching
    text = normalize_text(chunk_text)

    # Count how many query terms appear in the chunk text
    hits = sum(1 for term in query_terms if term in text)

    # Convert overlap into a ratio so the score scales across question lengths
    overlap_ratio = hits / len(query_terms)

    # Return a bounded lexical score
    return overlap_ratio * 0.30


# Reward chunks that contain the full query phrase
def compute_exact_phrase_score(normalized_query: str, chunk_text: str) -> float:
    # If the normalized query is empty, there is nothing to match
    if not normalized_query:
        return 0.0

    # Normalize the chunk text
    text = normalize_text(chunk_text)

    # Give a useful boost when the full query appears directly in the chunk
    if normalized_query in text:
        return 0.25

    return 0.0


# Reward chunks that look like definitions in a generic, field-independent way
def compute_definition_style_score(intent: str, chunk_text: str) -> float:
    # Only definition-like questions should receive this extra boost
    if intent != "definition":
        return 0.0

    # Normalize the chunk text
    text = normalize_text(chunk_text)

    # Generic definition-style phrases that work across many subjects
    definition_patterns = [
        " is a ",
        " is an ",
        " is the ",
        " refers to ",
        " defined as ",
        " can be defined as ",
        " means ",
        " describes ",
    ]

    # If any definition pattern appears, give a small boost
    if any(pattern in text for pattern in definition_patterns):
        return 0.10

    return 0.0


# Slightly prefer chunks that are not excessively long
def compute_chunk_length_adjustment(chunk_text: str) -> float:
    # Count how many words the chunk contains
    word_count = len(chunk_text.split())

    # Penalize very long chunks because they often mix multiple ideas together
    if word_count > 140:
        return -0.06

    # Slightly reward compact but still meaningful chunks
    if 35 <= word_count <= 110:
        return 0.04

    return 0.0


# Slightly penalize vague forward-reference phrases that often do not directly answer the question
def compute_vagueness_penalty(chunk_text: str) -> float:
    # Normalize the text
    text = normalize_text(chunk_text)

    # These phrases often indicate context-setting rather than direct answers
    vague_prefixes = [
        "we will",
        "later we",
        "we shall",
        "we are going to",
    ]

    # Penalize chunks that begin vaguely
    if any(text.startswith(prefix) for prefix in vague_prefixes):
        return -0.06

    return 0.0


# Combine semantic and lexical signals into a better reranked ordering
def rerank_chunks(query: str, chunks: list[dict]) -> list[dict]:
    # Normalize the full query once
    normalized_query = normalize_text(query)

    # Extract important query terms once
    query_terms = extract_query_terms(query)

    # Detect broad query intent once
    intent = detect_query_intent(query)

    # Store updated chunk objects here
    reranked_chunks = []

    # Score each candidate chunk
    for chunk in chunks:
        # Read the original semantic score produced by retrieval
        semantic_score = float(chunk.get("score", 0.0))

        # Read the transcript text safely
        chunk_text = chunk.get("text", "")

        # Compute generic lexical signals
        exact_phrase_score = compute_exact_phrase_score(normalized_query, chunk_text)
        keyword_overlap_score = compute_keyword_overlap_score(query_terms, chunk_text)
        definition_style_score = compute_definition_style_score(intent, chunk_text)
        length_adjustment = compute_chunk_length_adjustment(chunk_text)
        vagueness_penalty = compute_vagueness_penalty(chunk_text)

        # Combine all signals into one rerank score
        rerank_score = (
            semantic_score
            + exact_phrase_score
            + keyword_overlap_score
            + definition_style_score
            + length_adjustment
            + vagueness_penalty
        )

        # Save useful debugging info on the chunk itself
        chunk["rerank_score"] = rerank_score
        chunk["intent"] = intent
        chunk["keyword_overlap_score"] = keyword_overlap_score
        chunk["exact_phrase_score"] = exact_phrase_score
        chunk["definition_style_score"] = definition_style_score

        # Add the updated chunk to the output list
        reranked_chunks.append(chunk)

    # Sort by rerank score so the strongest candidate appears first
    reranked_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)

    # Return the reranked candidates
    return reranked_chunks