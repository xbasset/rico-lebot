from dotenv import load_dotenv

load_dotenv()
from flask import Flask, session, request, render_template
from core.config import APP_SECRET_KEY, LLM_MODEL, PRIVATE_ROLES_PATTERN_MATCH, SHOW_PRIVATE_ROLES

from extensions import socketio

from livekit import api
import os
from werkzeug.utils import secure_filename
import datetime

from openai import OpenAI

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
app.config["TEMPLATES_AUTO_RELOAD"] = True

socketio.init_app(app)

roles = []


def load_roles(show_private=SHOW_PRIVATE_ROLES):
    """ Load roles from the `roles folder`"""
    global roles
    roles = []
    for resource in os.listdir("roles"):
        if resource == "private" and show_private:
            for role in os.listdir("roles/private"):
                if os.path.isdir(f"roles/private/{role}"):
                    if PRIVATE_ROLES_PATTERN_MATCH:
                        for pattern in PRIVATE_ROLES_PATTERN_MATCH:
                            if pattern in role:
                                roles.append({"folder": f"{resource}/{role}", "name": role.replace("_", " ").replace("-", " ").title()})
                    else:
                        roles.append({"folder": f"{resource}/{role}", "name": role.replace("_", " ").replace("-", " ").title()})
        else:
            if resource != "__pycache__" and resource != "__init__.py" and resource != "private" and not show_private:
                if os.path.isdir(f"roles/{resource}"):
                    roles.append({"folder": resource, "name": resource.replace("_", " ").replace("-", " ").title()})
    # sort roles by name
    roles = sorted(roles, key=lambda x: x["name"])

        
        
        


@app.route("/", methods=["GET"])
def home():
    load_roles()
    return render_template("index.html", roles = roles)

@app.route("/run/<role>", methods=["GET"])
def role_route(role):
    try:
        global roles
        if role not in [r["folder"] for r in roles]:
            return {"error": "Role not found in request"}, 400
        
        session["role"] = role

        return render_template("run.html", role=role, role_name = [r["name"] for r in roles if r["folder"] == role][0])
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/run/private/<role>", methods=["GET"])
def private_role(role):
    try:
        return(role_route(f"private/{role}"))
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/agent/auth", methods=["GET"])
def get_token():
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    if "user_id" not in session:
        import uuid

        user_id = f"anon-{uuid.uuid4().hex[:5]}"
        user_name = "Anonymous"
    else:
        user_id = session["user_id"]
        user_name = session["user_name"]
    token = (
        api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
        .with_identity(f"ricoapp-user-{user_id}")
        .with_name(secure_filename(user_name))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=f"ricoapp-{timestamp}-{user_id}",
                can_update_own_metadata=True,
                room_record=True,
            )
        )
    )

    auth_data = {
        "url": f"{os.getenv('LIVEKIT_URL')}",
        "token": token.to_jwt(),
        "room": f"ricoapp-{timestamp}-{user_id}",
        "identity": f"ricoapp-user-{user_id}",
    }

    return auth_data


# an api to match the conversation transcription with the blog tags
@app.route("/api/recap", methods=["POST"])
def recap():
    try:
        data = request.json
        if "transcription" not in data or not data["transcription"] or data["transcription"] == "":
            return {"error": "Transcription not found in request"}
        transcription = data["transcription"]

        with open(f"roles/{session['role']}/recap.instruct") as f:
            instruction = f.read()

        client = OpenAI()
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "assistant", "content": [{"type": "text", "text": instruction}]},
                {
                    "role": "user",
                    "content": [{"type": "text", "text": transcription}],
                },
            ],
        )
        
        result = str(response.choices[0].message.content).replace("```markdown", "").replace("```", "")

        return {
            "summary": result,
        }
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/api/save", methods=["POST"])
def save():
    try:
        data = request.json
        if "information_to_save" not in data or not data["information_to_save"] or data["information_to_save"] == "":
            return {"error": "Information to save not found in request"}
        information_to_save = data["information_to_save"]
        agent_id = data["agent_id"]
        timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")
        with open(f"roles/{session['role']}/saved.txt", "a") as f:
            f.write(f"{timestamp} > {agent_id}: {information_to_save}\n")
        return {
            "summary": information_to_save,
        }
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)
