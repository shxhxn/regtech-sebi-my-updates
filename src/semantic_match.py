"""
Local, free, zero-API semantic matching between obligations.
Uses sentence-transformers (runs on Apple Silicon MPS automatically, no internet
needed after the one-time model download). Used to catch obligations that were
REWORDED between circular versions and would otherwise wrongly show as
"removed + added" instead of "modified" when diffing.
"""
import os
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import numpy as np

_MODEL = None

def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL

def _ob_text(ob):
    parts = [ob.get("title", ""), ob.get("summary", ""),
             ob.get("required_action", ""), ob.get("trigger", "")]
    return " . ".join(p for p in parts if p)

def embed_obligations(obligations):
    model = _get_model()
    texts = [_ob_text(o) for o in obligations]
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

def greedy_match(sims, threshold=0.72):
    """One-to-one greedy assignment: highest-similarity pairs win first."""
    n_old, n_new = sims.shape
    pairs = sorted(((sims[i][j], i, j) for i in range(n_old) for j in range(n_new)),
                   reverse=True, key=lambda x: x[0])
    used_old, used_new, matches = set(), set(), []
    for score, i, j in pairs:
        if score < threshold:
            break
        if i in used_old or j in used_new:
            continue
        used_old.add(i); used_new.add(j)
        matches.append((i, j, float(score)))
    return matches, used_old, used_new

def match_unmatched(old_list, new_list, threshold=0.72):
    """
    Run on the LEFTOVER obligations after exact-ID matching has already paired up
    everything it could. Finds reworded/renamed matches among what's left.
    Returns: matches=[(old_ob, new_ob, score), ...], unmatched_old, unmatched_new
    """
    if not old_list or not new_list:
        return [], list(old_list), list(new_list)

    old_emb = embed_obligations(old_list)
    new_emb = embed_obligations(new_list)
    sims = np.dot(old_emb, new_emb.T)  # vectors are normalized -> dot product = cosine similarity

    matches_idx, used_old, used_new = greedy_match(sims, threshold)
    matches = [(old_list[i], new_list[j], score) for i, j, score in matches_idx]
    unmatched_old = [o for k, o in enumerate(old_list) if k not in used_old]
    unmatched_new = [o for k, o in enumerate(new_list) if k not in used_new]
    return matches, unmatched_old, unmatched_new
