from rag.embedding_store import EmbeddingStore

def get_rag_context(query, k=3):
    store = EmbeddingStore()
    results = store.query(query, k=k)
    return "\n".join(results)
