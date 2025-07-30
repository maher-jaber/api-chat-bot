import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def get_top_k_answers(user_embedding, corpus_embeddings, faq_data, k=5):
    scores = cosine_similarity(user_embedding, corpus_embeddings)[0]
    top_k_idx = np.argsort(scores)[::-1][:k]
    return [
        {
            "question": faq_data[i]["question"],
            "answer": faq_data[i]["answer"],
            "score": float(scores[i])
        }
        for i in top_k_idx
    ]

def generate_response(top_answers: list, user_question: str):
    best_match = top_answers[0]
    suggested_questions = []
    
    # Seuil pour considérer une réponse comme exacte
    EXACT_MATCH_THRESHOLD = 0.75
    
    # 1. Réponse exacte (pas de suggestions)
    if best_match["score"] >= EXACT_MATCH_THRESHOLD:
        answer = best_match["answer"]
        return answer, None  # Aucune suggestion
    
    # 2. Réponse probable (suggestions similaires)
    elif best_match["score"] >= 0.5:
        answer = best_match["answer"]
        suggested_questions = [q["question"] for q in top_answers[1:3]]
    
    # 3. Réponse incertaine (suggestions génériques)
    else:
        answer = "Pouvez-vous préciser votre besoin ?"
        suggested_questions = [
            "Prendre un rendez-vous",
            "Annuler un rendez-vous",
            "Consulter les horaires"
        ]
    
    # Nettoyage des suggestions
    unique_suggestions = []
    seen = set()
    for q in suggested_questions:
        if q not in seen and q != user_question:  # Exclure la question actuelle
            seen.add(q)
            unique_suggestions.append(q)
    
    return answer, unique_suggestions[:3] if unique_suggestions else None