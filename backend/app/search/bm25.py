import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return re.findall(r'\b\w+\b', text.lower())


class BM25:
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_tokens = [tokenize(doc) for doc in documents]
        self.doc_len = [len(toks) for toks in self.doc_tokens]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0.0
        self.n_docs = len(documents)
        # document frequencies
        self.df = defaultdict(int)
        for toks in self.doc_tokens:
            for t in set(toks):
                self.df[t] += 1
        # idf
        self.idf = {}
        for t, f in self.df.items():
            self.idf[t] = math.log((self.n_docs - f + 0.5) / (f + 0.5) + 1.0)
    
    def score(self, query: str, doc_idx: int) -> float:
        query_tokens = tokenize(query)
        score = 0.0
        doc_toks = self.doc_tokens[doc_idx]
        dl = self.doc_len[doc_idx]
        tf = Counter(doc_toks)
        for q in query_tokens:
            if q not in tf:
                continue
            idf_q = self.idf.get(q, 0.0)
            f_qd = tf[q]
            denom = f_qd + self.k1 * (1 - self.b + self.b * dl / self.avgdl) if self.avgdl > 0 else f_qd
            score += idf_q * (f_qd * (self.k1 + 1)) / denom
        return score

    def top_k(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        scores = [(i, self.score(query, i)) for i in range(self.n_docs)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]
