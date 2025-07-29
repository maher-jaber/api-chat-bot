import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def get_top_k_answers(user_embedding, corpus_embeddings, faq_data, k=3):
    scores = cosine_similarity(user_embedding, corpus_embeddings)[0]
    top_k_idx = np.argsort(scores)[::-1][:k]
    results = [
        {"question": faq_data[i]["question"], "answer": faq_data[i]["answer"], "score": float(scores[i])}
        for i in top_k_idx
    ]
    return results