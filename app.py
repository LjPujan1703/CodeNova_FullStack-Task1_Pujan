from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def as_dict(self):
        return {"id": self.id, "title": self.title, "content": self.content,
                "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat()}

with app.app_context():
    db.create_all()

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/notes")
def list_notes():
    search = request.args.get("q", "").strip()
    query = Note.query
    if search:
        term = f"%{search}%"
        query = query.filter(db.or_(Note.title.ilike(term), Note.content.ilike(term)))
    notes = query.order_by(Note.updated_at.desc()).all()
    return jsonify([note.as_dict() for note in notes])

@app.post("/api/notes")
def create_note():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()
    if not title:
        return jsonify({"error": "Please enter a note title."}), 400
    if len(title) > 120:
        return jsonify({"error": "Title must be 120 characters or fewer."}), 400
    note = Note(title=title, content=content)
    db.session.add(note)
    db.session.commit()
    return jsonify(note.as_dict()), 201

@app.put("/api/notes/<int:note_id>")
def update_note(note_id):
    note = db.session.get(Note, note_id)
    if not note:
        return jsonify({"error": "Note not found."}), 404
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()
    if not title:
        return jsonify({"error": "Please enter a note title."}), 400
    if len(title) > 120:
        return jsonify({"error": "Title must be 120 characters or fewer."}), 400
    note.title, note.content = title, content
    db.session.commit()
    return jsonify(note.as_dict())

@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id):
    note = db.session.get(Note, note_id)
    if not note:
        return jsonify({"error": "Note not found."}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted."})

@app.errorhandler(500)
def server_error(_error):
    db.session.rollback()
    return jsonify({"error": "Something went wrong on the server. Please try again."}), 500

if __name__ == "__main__":
    app.run(debug=True)
