import json
from pathlib import Path

from app.config.settings import settings
from app.services.chat import ChatService

query = "What is 3GPP"

service = ChatService(session_id="forensics-3gpp")
retriever = service.retriever

print("QUERY:", query)
print("ROUTE:", service.router.route(query))
print("MIN_RETRIEVAL_SCORE:", settings.MIN_RETRIEVAL_SCORE)

# Dense search
query_embedding = retriever.embedding_generator.embed_text(query)
dense = retriever.vector_store.search(
    embedding=query_embedding,
    top_k=settings.VECTOR_TOP_K,
)
print("\nDENSE_RESULTS:")
for i, r in enumerate(dense, 1):
    p = r.payload
    print(json.dumps({
        "rank": i,
        "score": getattr(r, "score", None),
        "chunk_id": p.get("chunk_id"),
        "document": p.get("document"),
        "section": p.get("section"),
        "text": (p.get("text") or "")[:200],
    }, ensure_ascii=False))

# BM25
sparse = retriever.bm25.search(
    query=query,
    top_k=settings.BM25_TOP_K,
)
print("\nBM25_RESULTS:")
for i, r in enumerate(sparse, 1):
    print(json.dumps({
        "rank": i,
        "score": r.get("bm25_score"),
        "chunk_id": r.get("chunk_id"),
        "document": r.get("document"),
        "section": r.get("section"),
        "text": (r.get("text") or "")[:200],
    }, ensure_ascii=False))

# Merge
merged = retriever._merge_results(dense, sparse)
print("\nMERGED_RESULTS:")
for i, r in enumerate(merged, 1):
    print(json.dumps({
        "rank": i,
        "chunk_id": r.get("chunk_id"),
        "document": r.get("document"),
        "section": r.get("section"),
        "text": (r.get("text") or "")[:200],
    }, ensure_ascii=False))

# Rerank
reranked = retriever._rerank(query=query, documents=merged)
print("\nRERANKED_RESULTS:")
for i, r in enumerate(reranked, 1):
    print(json.dumps({
        "rank": i,
        "relevance_score": r.get("rerank_score"),
        "chunk_id": r.get("chunk_id"),
        "document": r.get("document"),
        "section": r.get("section"),
        "text": (r.get("text") or "")[:200],
    }, ensure_ascii=False))

# Final chunks sent to LLM
final = retriever.retrieve(query)
print("\nFINAL_LLM_CHUNKS:")
for i, r in enumerate(final, 1):
    print(json.dumps({
        "rank": i,
        "relevance_score": r.get("rerank_score"),
        "chunk_id": r.get("chunk_id"),
        "document": r.get("document"),
        "section": r.get("section"),
        "text": (r.get("text") or "")[:200],
    }, ensure_ascii=False))

# Exact prompt constructed before LLM call
if service.router.route(query) == "GENERAL":
    messages = [{"role": "system", "content": service.system_prompt}]
    messages.extend(service.memory.get_history())
    messages.append({"role": "user", "content": query})
else:
    context = "\n\n".join(chunk["text"] for chunk in final)
    messages = [{"role": "system", "content": service.system_prompt}]
    messages.extend(service.memory.get_history())
    messages.append({
        "role": "user",
        "content": f"""Answer ONLY using the retrieved knowledge.\n\nQuestion:\n{query}\n\nRetrieved Context:\n{context}\n""",
    })

print("\nLLM_PROMPT:")
for m in messages:
    print("---")
    print(m["role"])
    print(m["content"])
