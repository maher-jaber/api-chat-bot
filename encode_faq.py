import json
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')

with open('faq.json', 'r', encoding='utf-8') as f:
    faq = json.load(f)

questions = [item['question'] for item in faq]
embeddings = model.encode(questions, convert_to_numpy=True)

np.save('embeddings.npy', embeddings)
print("✅ Embeddings générés et sauvegardés.")