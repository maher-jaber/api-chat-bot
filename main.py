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
from scenario_manager import ScenarioManager



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

THRESHOLD = 0.5  # Seuil légèrement abaissé pour plus de couverture
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
    id: Optional[int] = None
    type: str  # "simple" ou "scenario"
    question: str
    answer: str
    scenario: Optional[dict] = None

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




scenario_manager = ScenarioManager()

@app.post("/ask", response_model=AnswerResponse)
async def ask(req: QuestionRequest):
    # Vérifier d'abord si l'utilisateur est dans un scénario actif
    if req.session_id in scenario_manager.active_scenarios:
        scenario_response = scenario_manager.handle_scenario_step(req.session_id, req.message)
        if scenario_response:
            memory_store.add_message(req.session_id, req.message, scenario_response)
            return AnswerResponse(
                answer=scenario_response,
                confidence=1.0,  # Confiance élevée pour les réponses de scénario
                history=memory_store.get_history(req.session_id),
                suggested_questions=["Quitter le scénario"]  # Suggestion pour sortir du scénario
            )

    # Traitement normal des FAQ
    user_embedding = model.encode([req.message], convert_to_numpy=True)
    top_answers = get_top_k_answers(user_embedding, embeddings, faq, k=TOP_K)
    best_match = top_answers[0]

    # Vérifier si la meilleure correspondance est un lanceur de scénario
    if best_match["score"] >= THRESHOLD and "scenario" in best_match and best_match["scenario"]:
        # Démarrer le scénario
        scenario_manager.start_scenario(req.session_id, best_match["scenario"])
        initial_response = best_match["answer"]
        if best_match["scenario"]["steps"]:
            initial_response += f"\n\n{best_match['scenario']['steps'][0]['question']}"
        
        memory_store.add_message(req.session_id, req.message, initial_response)
        return AnswerResponse(
            answer=initial_response,
            confidence=round(best_match["score"], 2),
            history=memory_store.get_history(req.session_id),
            suggested_questions=["Quitter le scénario"]
        )

    # Génération de réponse standard pour les FAQ simples
    answer, suggested_questions = generate_response(top_answers, req.message)
    
    # Journalisation des questions non comprises
    if best_match["score"] < THRESHOLD:
        logging.info("", extra={
            "session_id": req.session_id,
            "score": best_match["score"],
            "question": req.message
        })
        with open("not_answered.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | score={best_match['score']:.3f} | question={req.message}\n")

    # Mise à jour de l'historique de session
    memory_store.add_message(req.session_id, req.message, answer)

    return AnswerResponse(
        answer=answer,
        confidence=round(best_match["score"], 2),
        history=memory_store.get_history(req.session_id),
        suggested_questions=suggested_questions
    )
    
@app.post("/reload")
def reload_data():
    global faq, embeddings
    with open('faq.json', 'r', encoding='utf-8') as f:
        faq = json.load(f)
    
    # Regénérer les embeddings comme dans encode_faq.py
    all_questions = []
    for item in faq:
        all_questions.append(item['question'])
        if item['type'] == 'scenario' and item['scenario']:
            for step in item['scenario']['steps']:
                for answer in step['answers']:
                    clean_pattern = answer['pattern'].replace('.*', '').strip()
                    if clean_pattern and clean_pattern != '.':
                        all_questions.append(clean_pattern)
    
    embeddings = model.encode(all_questions, convert_to_numpy=True)
    np.save('embeddings.npy', embeddings)
    return {"status": "FAQ rechargée avec succès"}



@app.get("/faq", response_model=List[dict])
def list_faq():
    with open(FAQ_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.post("/faq")
def add_faq(item: FAQItem):
    with open(FAQ_PATH, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        new_id = max([e.get("id", 0) for e in data], default=0) + 1
        new_item = {
            "id": new_id,
            "type": item.type,
            "question": item.question,
            "answer": item.answer,
            "scenario": item.scenario
        }
        data.append(new_item)
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
                faq.update({
                    "type": item.type,
                    "question": item.question,
                    "answer": item.answer,
                    "scenario": item.scenario
                })
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
