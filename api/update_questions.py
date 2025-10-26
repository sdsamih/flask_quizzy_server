import requests
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def fetch_questions():
    
    #verificar se já foi atualizado hoje (o script roda a cada 24h e quando o servidor inicia/reinicia)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MAX(created_at) AS last_update FROM questions"))
        row = result.mappings().fetchone() 
        if row and row["last_update"]:
            last_update = row["last_update"]
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update)
            now = datetime.utcnow()
            delta = now - last_update
            if delta < timedelta(hours=24):#nao atualizar ainda
                return
    
    #questoes antigas, deve atualizar
    response = requests.get("https://opentdb.com/api.php?amount=10&type=multiple")
    data = response.json()
    
    if data["response_code"] != 0:
        print("Falha na API")
        return
    
    questions = [{
        "question": q["question"],
        "correct_answer": q["correct_answer"],
        "incorrect_answers": str(q["incorrect_answers"])
    } for q in data["results"]]
    
    with engine.connect() as conn:
        # Limpa perguntas antigas
        conn.execute(text("DELETE FROM questions"))
        # Insere novas perguntas
        for q in questions:
            conn.execute(
                text(
                    "INSERT INTO questions (question, correct_answer, incorrect_answers) VALUES (:question, :correct_answer, :incorrect_answers)"
                ), **q
            )
    print("Perguntas atualizadas com sucesso.")

if __name__ == "__main__":
    fetch_questions()
