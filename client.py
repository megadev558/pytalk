from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import json, uuid

app = Flask(__name__)
app.secret_key = "pysecret"
socketio = SocketIO(app, manage_session=False)

USER_FILE = "users.json"
messages = []
connected_users = {}

# Gestion utilisateurs
def load_users():
    try: return json.load(open(USER_FILE))
    except: return []

def save_users(data):
    json.dump(data, open(USER_FILE, "w"))

@app.route("/")
def home():
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        pseudo = request.form["pseudo"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        users = load_users()
        if any(u["email"] == email for u in users):
            return render_template("register.html", error="Email déjà utilisé")
        users.append({"pseudo": pseudo, "email": email, "password": password})
        save_users(users)
        session["user"] = pseudo
        return redirect("/chat")
    return render_template("register.html", error=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        for u in load_users():
            if u["email"] == email and check_password_hash(u["password"], password):
                session["user"] = u["pseudo"]
                return redirect("/chat")
        return render_template("login.html", error="Email ou mot de passe incorrect")
    return render_template("login.html", error=None)

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/login")
    return render_template("chat.html", user=session["user"], messages=messages)

@socketio.on("connect")
def connect():
    user_id = str(uuid.uuid4())
    connected_users[user_id] = session.get("user", "Anonyme")
    emit("user_list", list(connected_users.values()), broadcast=True)
    emit("your_id", {"id": user_id})

@socketio.on("disconnect")
def disconnect():
    # suppression simplifiée
    emit("user_list", list(connected_users.values()), broadcast=True)

@socketio.on("signal")
def signal(data):
    emit("signal", data, broadcast=True)

@socketio.on("message")
def handle_msg(data):
    messages.append(data)
    emit("message", data, broadcast=True)

@socketio.on("logout")
def logout_user():
    session.clear()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, allow_unsafe_werkzeug=True)