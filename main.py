# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import json
from datetime import datetime
from rag_utils import get_top_k_answers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open('faq.json', 'r', encoding='utf-8') as f:
    faq = json.load(f)

embeddings = np.load('embeddings.npy')
model = SentenceTransformer('all-mpnet-base-v2')

THRESHOLD = 0.5

class QuestionRequest(BaseModel):
    message: str

class AnswerResponse(BaseModel):
    answer: str
    confidence: float

@app.post("/ask", response_model=AnswerResponse)
async def ask(req: QuestionRequest):
    user_embedding = model.encode([req.message])
    top_answers = get_top_k_answers(user_embedding, embeddings, faq, k=3)

    best = top_answers[0]
    if best["score"] >= THRESHOLD:
        return {
            "answer": best["answer"],
            "confidence": round(best["score"], 2)
        }
    else:
        with open("not_answered.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | score={best['score']:.3f} | question={req.message}\n")

        return {
            "answer": "Je n’ai pas bien compris votre question. Pouvez-vous reformuler ?",
            "confidence": 0
        }

