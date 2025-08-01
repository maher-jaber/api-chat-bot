import json
from collections import defaultdict

def convert_faq_format():
    # Charger les données d'entrée
    with open('old.json', 'r', encoding='utf-8') as f:
        faq_data = json.load(f)
    
    # Grouper les questions similaires par réponse
    answer_groups = defaultdict(list)
    for item in faq_data:
        # Ignorer les entrées de test informelles
        if item['answer'].lower() in ["haha", "rep", "loooool", "zohra", "ta77an", "ok"]:
            continue
        answer_groups[item['answer']].append(item['question'])
    
    # Convertir en nouveau format
    output_data = []
    id_counter = 1
    
    # Ajouter les questions simples
    for answer, questions in answer_groups.items():            
        if len(questions) == 1:
            output_data.append({
                "id": id_counter,
                "type": "simple",
                "question": questions[0],
                "answer": answer,
                "scenario": None
            })
            id_counter += 1
        else:
            # Pour les groupes de questions avec la même réponse, créer un scénario
            scenario = {
                "steps": [
                    {
                        "question": "Pouvez-vous préciser votre demande ?",
                        "answers": []
                    }
                ],
                "exit_phrases": ["annuler", "stop", "quitter"]
            }
            
            # Ajouter toutes les variantes de questions comme réponses possibles
            for question in questions:
                cleaned_question = question.lower().replace('?', '').replace('.', '')
                scenario["steps"][0]["answers"].append({
                    "pattern": f".*{cleaned_question}.*",
                    "response": answer
                })
            
            # Ajouter une réponse par défaut
            scenario["steps"][0]["answers"].append({
                "pattern": ".*",
                "response": answer
            })
            
            output_data.append({
                "id": id_counter,
                "type": "scenario",
                "question": questions[0],  # Utiliser la première question comme représentante
                "answer": answer,
                "scenario": scenario
            })
            id_counter += 1
    
    # Sauvegarder le résultat
    with open('faq.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("Conversion terminée! Le nouveau fichier 'faq.json' a été créé.")

# Exécuter la conversion
convert_faq_format()