from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from update_questions import fetch_questions
from datetime import datetime, timedelta, timezone
import os

app = Flask(__name__)

# Lê a URL do banco da variável de ambiente
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    incorrect_answers = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

class Ranking(db.Model):
    __tablename__ = "ranking"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

#cria tabelas se não existirem
with app.app_context():
    db.create_all()
    # Chama fetch_questions uma vez quando o servidor inicia
    fetch_questions()

#retorna questoes de hoje
@app.route("/daily_quiz")
def daily_quiz():
    # Atualiza apenas se necessário
    fetch_questions()  
    
    questions = Question.query.order_by(Question.created_at.desc()).limit(10).all()
    results = [
        {
            "question": q.question,
            "correct_answer": q.correct_answer,
            "incorrect_answers": q.incorrect_answers,
        }
        for q in questions
    ]
    return jsonify({"response_code": 0, "results": results})

#recebe a pontuacao do usuario
@app.route("/submit_score", methods=["POST"])
def submit_score():
    data = request.get_json()
    name = data.get("name")
    score = data.get("score")

    if not name or score is None:
        return jsonify({"error": "name and score required"}), 400

    ranking_entry = Ranking(name=name, score=score)
    db.session.add(ranking_entry)
    db.session.commit()

    return jsonify({"status": "ok"})

#retorna o ranking
@app.route("/ranking")
def get_ranking():
    ranking = Ranking.query.order_by(Ranking.score.desc(), Ranking.created_at.asc()).all()
    results = [
        {"name": r.name, "score": r.score, "created_at": r.created_at.isoformat()}
        for r in ranking
    ]
    return jsonify({"ranking": results})

#limpar ranking (entries com >24h)
def clean_old_ranking():
    with app.app_context():
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)
        Ranking.query.filter(Ranking.created_at < cutoff).delete()
        db.session.commit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
