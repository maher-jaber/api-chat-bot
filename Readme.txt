pip install numpy sentence-transformers scikit-learn ou pip3 install numpy sentence-transformers scikit-learn
python encode_faq.py


hebergement
pip install "uvicorn[standard]" gunicorn fastapi
gunicorn faq_server:app -c gunicorn_conf.py


local
pip install fastapi uvicorn
uvicorn faq_server:app --host 127.0.0.1 --port 8000


curl -X POST -H "Content-Type: application/json" \
  -d '{"message":"Je veux parler à un docteur"}' \
  http://localhost:8000/ask.php



python3 answer.py "je veux voir un médecin"