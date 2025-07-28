from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json

app = FastAPI()
# Ajoute le middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou remplace par ["http://localhost:5173"] si tu veux limiter
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Charger les données une seule fois au démarrage
with open('faq.json', 'r', encoding='utf-8') as f:
    faq = json.load(f)

embeddings = np.load('embeddings.npy')  # Format: np.ndarray [nb_questions, 384]
model = SentenceTransformer('all-MiniLM-L6-v2')

THRESHOLD = 0.45

class QuestionRequest(BaseModel):
    message: str

class AnswerResponse(BaseModel):
    answer: str
    confidence: float

@app.post("/ask", response_model=AnswerResponse)
async def ask(req: QuestionRequest):
    user_embedding = model.encode([req.message])
    scores = cosine_similarity(user_embedding, embeddings)[0]
    best_index = int(np.argmax(scores))
    best_score = float(scores[best_index])

    if best_score >= THRESHOLD:
        return {
            "answer": faq[best_index]["answer"],
            "confidence": round(best_score, 2)
        }
    else:
        return {
            "answer": "Je n’ai pas bien compris votre question. Pouvez-vous reformuler ?",
            "confidence": 0
        }
