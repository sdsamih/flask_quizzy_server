from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
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
    incorrect_answers = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route("/daily_quiz")
def daily_quiz():
    questions = Question.query.limit(10).all()
    results = [
        {
            "question": q.question,
            "correct_answer": q.correct_answer,
            "incorrect_answers": q.incorrect_answers
        }
        for q in questions
    ]
    return jsonify({"response_code": 0, "results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
