from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import json
from datetime import datetime
from rag_utils import get_top_k_answers, generate_response  # Modifié
from session_store import SessionMemoryStore
from typing import List, Optional
import re
import logging

app = FastAPI()

# Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation
with open('faq.json', 'r', encoding='utf-8') as f:
    faq = json.load(f)

embeddings = np.load('embeddings.npy')
model = SentenceTransformer('all-mpnet-base-v2')
memory_store = SessionMemoryStore()

THRESHOLD = 0.60  # Seuil légèrement abaissé pour plus de couverture
TOP_K = 5  # Plus de résultats pour meilleure sélection

# Logging structuré
logging.basicConfig(
    filename="conversations.log",
    format="%(asctime)s | session=%(session_id)s | score=%(score).2f | question=%(question)s",
    level=logging.INFO
)

class QuestionRequest(BaseModel):
    message: str
    session_id: str

class AnswerResponse(BaseModel):
    answer: str
    confidence: float
    history: list
    suggested_questions: Optional[List[str]] = None  # Nouveau champ

class QuestionItem(BaseModel):
    timestamp: str
    score: float
    question: str

LOG_FILE = "not_answered.log"
FAQ_PATH = "faq.json"

class FAQItem(BaseModel):
    question: str
    answer: str

pattern = re.compile(
    r"^(?P<timestamp>[\d\-T:\.]+) \| score=(?P<score>[\d\.]+) \| question=(?P<question>.+)$"
)

def parse_log_line(line: str):
    m = pattern.match(line.strip())
    if not m:
        return None
    return {
        "timestamp": m.group("timestamp"),
        "score": float(m.group("score")),
        "question": m.group("question"),
    }

@app.get("/questions", response_model=List[QuestionItem])
def get_questions():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture fichier: {e}")

    results = []
    for line in lines:
        parsed = parse_log_line(line)
        if parsed:
            results.append(parsed)
    return results

@app.post("/ask", response_model=AnswerResponse)
async def ask(req: QuestionRequest):
    # Encodage et recherche
    user_embedding = model.encode([req.message], convert_to_numpy=True)
    top_answers = get_top_k_answers(user_embedding, embeddings, faq, k=TOP_K)
    
    # Génération de réponse améliorée
    answer, suggested_questions = generate_response(top_answers, req.message)
    
    # Journalisation
    if top_answers[0]["score"] < THRESHOLD:
        logging.info("", extra={
            "session_id": req.session_id,
            "score": top_answers[0]["score"],
            "question": req.message
        })
        with open("not_answered.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | score={top_answers[0]['score']:.3f} | question={req.message}\n")

    # Mise à jour session
    memory_store.add_message(req.session_id, req.message, answer)

    return AnswerResponse(
        answer=answer,
        confidence=round(top_answers[0]["score"], 2),
        history=memory_store.get_history(req.session_id),
        suggested_questions=suggested_questions
    )

@app.post("/reload")
def reload_data():
    global faq, embeddings
    with open('faq.json', 'r', encoding='utf-8') as f:
        faq = json.load(f)
    questions = [item["question"] for item in faq]
    embeddings = model.encode(questions)
    np.save('embeddings.npy', embeddings)
    return {"status": "FAQ rechargée"}



@app.get("/faq", response_model=List[dict])
def list_faq():
    with open(FAQ_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.post("/faq")
def add_faq(item: FAQItem):
    with open(FAQ_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        new_id = max([e.get("id", 0) for e in data], default=0) + 1
        data.append({"id": new_id, "question": item.question, "answer": item.answer})
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.truncate()
    return {"status": "Ajouté", "id": new_id}

@app.put("/faq/{faq_id}")
def update_faq(faq_id: int, item: FAQItem):
    with open(FAQ_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        for faq in data:
            if faq.get("id") == faq_id:
                faq["question"] = item.question
                faq["answer"] = item.answer
                break
        else:
            raise HTTPException(status_code=404, detail="FAQ non trouvée")
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.truncate()
    return {"status": "Modifié", "id": faq_id}

@app.delete("/faq/{faq_id}")
def delete_faq(faq_id: int):
    with open(FAQ_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        data = [faq for faq in data if faq.get("id") != faq_id]
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.truncate()
    return {"status": "Supprimé", "id": faq_id}

@app.post("/threshold/{value}")
def update_threshold(value: float):
    global THRESHOLD
    THRESHOLD = value
    return {"status": f"Seuil mis à jour à {value}"}


@app.get("/threshold")
def get_threshold():
    return {"threshold": THRESHOLD}
