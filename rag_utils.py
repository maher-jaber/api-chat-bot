import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def safe_get_faq_item(faq_data, index):
    """Récupère un item FAQ en toute sécurité avec valeurs par défaut"""
    if not isinstance(faq_data, list) or index >= len(faq_data):
        return {
            "id": index,
            "question": f"Question par défaut {index}",
            "answer": "Réponse par défaut",
            "type": "simple",
            "scenario": None
        }
    return faq_data[index]

def get_top_k_answers(user_embedding, corpus_embeddings, faq_data, k=5):
    """Version ultra-robuste qui ne peut pas échouer"""
    try:
        # Validation des entrées
        if (not isinstance(faq_data, list) or 
            not isinstance(corpus_embeddings, np.ndarray) or
            len(faq_data) == 0 or 
            len(corpus_embeddings) == 0):
            return []

        # Calcul des similarités (protégé)
        try:
            scores = cosine_similarity(user_embedding, corpus_embeddings)[0]
        except:
            scores = np.zeros(len(corpus_embeddings))

        # Sélection des K meilleurs indices VALIDES
        valid_indices = [i for i in range(len(scores)) if i < len(faq_data)]
        sorted_indices = sorted(valid_indices, key=lambda i: -scores[i])
        top_k_idx = sorted_indices[:min(k, len(sorted_indices))]

        # Construction des réponses
        top_answers = []
        for i in top_k_idx:
            item = safe_get_faq_item(faq_data, i)
            top_answers.append({
                "score": float(scores[i]),
                "id": item.get("id", i),
                "type": item.get("type", "simple"),
                "question": item.get("question", f"Question {i}"),
                "answer": item.get("answer", "Réponse non disponible"),
                "scenario": item.get("scenario")
            })

        return top_answers

    except Exception as e:
        print(f"ERREUR: {str(e)} - Retourne une liste vide")
        return []

def generate_response(top_answers: list, user_question: str):
    """Génère une réponse toujours valide"""
    if not top_answers:
        return "Je n'ai pas compris. Pouvez-vous reformuler ?", ["Contact support", "Voir l'aide"]
    
    best_match = top_answers[0]
    answer = best_match.get("answer", "Je ne peux pas répondre pour le moment")
    
    # Seuils ajustables
    if best_match.get("score", 0) >= 0.75:
        return answer, None
    elif best_match.get("score", 0) >= 0.5:
        suggestions = [q.get("question", "") for q in top_answers[1:3] if isinstance(q, dict)]
        return answer, [s for s in suggestions if s and s != user_question][:2]
    else:
        return "Pouvez-vous préciser ?", ["Rendez-vous", "Annulation", "Horaires"]