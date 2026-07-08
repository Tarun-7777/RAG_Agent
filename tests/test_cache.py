from app.services.cache import generate_cache_key, get_cached_response, set_cached_response

def test_cache_key_generation():
    key1 = generate_cache_key("test question", "doc_1", 5)
    key2 = generate_cache_key("test question", "doc_1", 5)
    key3 = generate_cache_key("different question", "doc_1", 5)
    
    assert key1 == key2
    assert key1 != key3

def test_in_memory_fallback():
    key = generate_cache_key("What is AI?", "doc_123", 3)
    
    # Test Cache Miss
    assert get_cached_response(key) is None
    
    # Store response
    cached_data = {
        "answer": "Artificial Intelligence...",
        "sources": [{"document": "test.txt", "page": 1, "chunk_preview": "..."}]
    }
    set_cached_response(key, cached_data)
    
    # Test Cache Hit
    hit_data = get_cached_response(key)
    assert hit_data is not None
    assert hit_data["answer"] == "Artificial Intelligence..."
    assert hit_data["sources"][0]["document"] == "test.txt"
