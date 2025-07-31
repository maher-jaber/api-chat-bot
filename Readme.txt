pip install numpy sentence-transformers scikit-learn ou pip3 install numpy sentence-transformers scikit-learn
python encode_faq.py


hebergement
pip install "uvicorn[standard]" gunicorn fastapi
gunicorn faq_server:app -c gunicorn_conf.py


local
# Installer les dépendances
pip install -r requirements.txt

# Générer les embeddings
python encode_faq.py

# Lancer l’API
uvicorn main:app --reload


curl -X POST -H "Content-Type: application/json" \
  -d '{"message":"Je veux parler à un docteur"}' \
  http://localhost:8000/ask.php

Accès API :
👉 http://127.0.0.1:8000/docs

python3 answer.py "je veux voir un médecin"

# Installation
pip install -r requirements.txt

# Initialisation de la base SQLite
python init_db.py

# Génération des embeddings
python encode_faq.py

# Lancement de l'API
uvicorn main:app --reload

# Accès à l'interface Swagger
http://localhost:8000/docs

# Nettoyage des anciennes sessions (à mettre dans un cron)
python -c "from session_store import SessionDBStore; SessionDBStore().cleanup_old_sessions()"