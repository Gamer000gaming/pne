from flask import Flask, request, jsonify

app = Flask(__name__)

users = {}

messages = {}

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data["username"]
    pub_x_b64 = data["public_key"]  

    if username in users:
        return "Username already exists", 400

    users[username] = pub_x_b64
    messages[username] = []
    return "User registered"

@app.route("/pubkey/<username>")
def pubkey(username):
    if username not in users:
        return "User not found", 404
    return users[username]

@app.route("/receive", methods=["POST"])
def receive():
    data = request.json
    to = data["to"].split('@')[0]  
    if to not in messages:
        return "Recipient not found", 404
    messages[to].append(data)
    return "Message stored"

@app.route("/fetch/<username>")
def fetch(username):
    if username not in messages:
        return jsonify([])  
    return jsonify(messages[username])

@app.route("/confirm_fetch/<username>", methods=["POST"])
def confirm_fetch(username):
    if username not in messages:
        return "User not found", 404
    to_delete = request.json  
    messages[username] = [m for m in messages[username] if m['hash'] not in {x['hash'] for x in to_delete}]
    return "Deleted"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=16361)
