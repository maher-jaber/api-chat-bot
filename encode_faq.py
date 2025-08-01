import json
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')

with open('faq.json', 'r', encoding='utf-8') as f:
    faq = json.load(f)

# Collecter toutes les questions et variantes
all_questions = []
for item in faq:
    # Ajouter la question principale
    all_questions.append(item['question'])
    
    # Pour les scénarios, ajouter les patterns des réponses
    if item['type'] == 'scenario' and item['scenario']:
        for step in item['scenario']['steps']:
            for answer in step['answers']:
                # Extraire le motif sans les .* pour une meilleure représentation
                clean_pattern = answer['pattern'].replace('.*', '').strip()
                if clean_pattern and clean_pattern != '.':
                    all_questions.append(clean_pattern)

# Générer les embeddings pour toutes les questions
embeddings = model.encode(all_questions, convert_to_numpy=True)

np.save('embeddings.npy', embeddings)
print(f"✅ Embeddings générés pour {len(all_questions)} questions et sauvegardés.")