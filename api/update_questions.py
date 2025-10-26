import requests
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta, timezone
import json  # para converter listas em JSON válido

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def fetch_questions():
    # Verificar se já foi atualizado nas últimas 24h
    with engine.begin() as conn:
        result = conn.execute(text("SELECT MAX(created_at) AS last_update FROM questions"))
        row = result.mappings().fetchone() 
        if row and row["last_update"]:
            last_update = row["last_update"]
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update)
            if last_update.tzinfo is None: #NAO SUBTRAIR DATAS NAIVE COM DATAS AWARE
                last_update = last_update.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            delta = now - last_update
            if delta < timedelta(hours=24):
                return   #se <24h desde ultima atualizacao, nao altera nada no banco

    # Buscar novas perguntas da API
    response = requests.get("https://opentdb.com/api.php?amount=10&type=multiple")
    data = response.json()
    
    if data["response_code"] != 0:
        print("Falha na API")
        return
    
    questions = [{
        "question": q["question"],
        "correct_answer": q["correct_answer"],
        "incorrect_answers": json.dumps(q["incorrect_answers"])  # lista pra json
    } for q in data["results"]]
    
    #depois de fazer parse da resposta da api, atualiza o banco em si
    with engine.begin() as conn:
        # Limpa perguntas antigas (>24H)
        conn.execute(text("DELETE FROM questions"))
        # Adiciona perguntas novas
        for q in questions:
            q["created_at"] = datetime.now(timezone.utc)
            conn.execute(
                text(
                    "INSERT INTO questions (question, correct_answer, incorrect_answers, created_at) "
                    "VALUES (:question, :correct_answer, :incorrect_answers, :created_at)"
                ),
                q
            )
    print("Perguntas atualizadas com sucesso.")

if __name__ == "__main__":
    fetch_questions()
