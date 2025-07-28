# -*- coding: utf-8 -*-
import sys
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Forcer la sortie stdout en UTF-8 (Windows spécifique)
if sys.version_info >= (3, 7):
    sys.stdout.reconfigure(encoding='utf-8')

# Charger la FAQ et les embeddings
with open('faq.json', 'r', encoding='utf-8') as f:
    faq = json.load(f)

embeddings = np.load('embeddings.npy')
model = SentenceTransformer('all-MiniLM-L6-v2')

# Question reçue en argument CLI
user_question = sys.argv[1]

# Encoder la question
user_embedding = model.encode([user_question], convert_to_numpy=True)

# Similarités
scores = cosine_similarity(user_embedding, embeddings)[0]
best_index = np.argmax(scores)
best_score = scores[best_index]

# Seuil de confiance
THRESHOLD = 0.45

if best_score >= THRESHOLD:
    result = {
        "answer": faq[best_index]['answer'],
        "confidence": round(float(best_score), 2)
    }
else:
    result = {
        "answer": "Je n’ai pas bien compris votre question. Pouvez-vous reformuler ?",
        "confidence": 0
    }

print(json.dumps(result, ensure_ascii=False))
