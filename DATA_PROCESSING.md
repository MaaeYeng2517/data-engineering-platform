# Data Processing

## Full Pipeline: Extract → Clean → Normalize → Chunk → Entities

```mermaid
flowchart LR
    A["Raw content"] --> B["extract()"]
    B --> C["clean()"]
    C --> D["normalize()"]
    D --> E["chunk()"]
    E --> F["extract_entities()"]
    F --> G["Store"]
```

## Data Extract

`TextProcessor.extract(content, source_type)` dispatches by source type:

| Source | Method | What it does |
|---|---|---|
| `web` | `_extract_web()` | Strips HTML tags via regex `<[^>]+>`, collapses whitespace |
| `pdf` | `_extract_pdf()` | **Placeholder** — returns content as-is |
| `file` | `_extract_file()` | Returns content as-is |

## Data Clean

`TextProcessor.clean(text)` — two regex passes:

1. `re.sub(r'\s+', ' ', text)` — collapse all whitespace to single spaces
2. `re.sub(r'[^\w\s.,;:!?()\-\'\"{}[\]]', '', text)` — strip everything except word chars, digits, punctuation, quotes, brackets, braces

## Data Normalize

`TextProcessor.normalize(text)` — lowercase + strip. Applied **after** clean, so chunking and entity extraction run on lowercased text.

## Data Chunk

`Chunker.chunk(text)` — sliding window over characters:

- **Size:** 800 chars, **Overlap:** 100 chars
- Each chunk carries: `content`, `chunk_index`, `start_char`, `end_char`, `token_count` (whitespace split count)
- Identity is **positional only** — `chunk_index` resets per document, not stable across re-indexing

## Data Entities

`EntityExtractor.extract(text)` — naive regex over first 1000 chars:

- Splits on whitespace, flags words starting with uppercase and length > 2
- Type is always `"UNKNOWN"` — **no NER model wired up** (spaCy/BERT noted as placeholder)

## Index Path: TokenChunker

`TokenChunker` (`services/chunking.py`) — token-aware, used by the indexing task:

- **Size:** 300 tokens, **Overlap:** 50 tokens
- `TOKEN_RE = r"\S+"` — tokens are whitespace-delimited non-space runs
- Stable `chunk_id = f"{document_id}:{index}"` — survives re-indexing
- Carries: `chunk_id`, `content`, `metadata`, `token_count`, `chunk_index`, `start_char`, `end_char`

## Hybrid Index → Search

```mermaid
flowchart LR
    A["Document content"] --> B["TokenChunker<br/>300 tokens, 50 overlap"]
    B --> C["EmbeddingService.embed()"]
    C --> C1{"OPENAI_API_KEY?"}
    C1 -->|yes| C2["OpenAI · 1536/3072 dims"]
    C1 -->|no| C3["Offline hashing trick<br/>384 dims, deterministic"]
    C2 --> D[(VectorIndex)]
    C3 --> D
    B --> E[(KeywordIndex)]
    B --> F[(MetadataIndex)]
    D --> G[HybridIndex]
    E --> G
    F --> G
    G --> H["RetrievalEngine.search()"]
```

## Hybrid Search Scoring

```mermaid
flowchart TD
    Q["Query"] --> K["KeywordIndex<br/>1 / (1 + occurrences)"]
    Q --> V["VectorIndex<br/>cosine similarity"]
    K --> M["Merge by document"]
    V --> M
    M --> H["0.4 × keyword + 0.6 × vector"]
    H --> F["Metadata filter<br/>exact match"]
    F --> R["Rerank<br/>0.5 hybrid + 0.3 lexical<br/>+ 0.1 position + 0.1 length"]
    R --> OUT["top_k results"]
```

## RAG Answer Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant U as Browser
    participant A as POST /rag/
    participant R as RetrievalEngine
    participant C as ContextBuilder
    participant G as LLMGateway

    U->>A: {query, kb_ids}
    A->>R: search(query, kb_ids, limit)
    R-->>A: ranked passages
    A->>C: build(query, passages)
    Note over C: dedupe → filter → compress (500 chars)<br/>→ order → 4000-token budget
    C-->>A: context, sources, total_tokens
    A->>G: generate(messages, system=passages)
    G->>P: provider chain (openai → anthropic → google → ollama → offline)
    alt provider answered
        P-->>G: text + usage
        G-->>A: answer
    else provider failed
        G-->>A: degraded
        A->>A: extractive fallback — quote passages verbatim
    end
    A-->>U: answer, sources, citations, latency_ms, token_usage
```

## Current Limitations

- **Upload stores chunks, but nothing indexes them** — uploaded documents can't be searched
- **PDF extraction is a placeholder** — returns raw content as-is
- **Entity extraction is naive regex** — type is always `"UNKNOWN"`, no NER model
- **Qdrant/Elasticsearch** health-probed only; vector search is a numpy scan, keyword is term counting
- **`kb_ids` and `score_threshold`** accepted but ignored by the retrieval engine
- **Cross-process visibility** — `hybrid_index` is per-process; API and worker are separate containers
- **`chunks`, `entities`, `relationships`** tables declared in models but never written