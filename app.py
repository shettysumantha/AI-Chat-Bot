
from flask import Flask, request, jsonify, send_from_directory
from models.chatbot import Chatbot
from database.db import init_db, save_message

app = Flask(__name__, static_folder="static")
bot = Chatbot()

init_db()

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message","")
    response = bot.get_response(message)
    save_message(message, response)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
