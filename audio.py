from flask import Flask, jsonify, request, render_template
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, IAudioSessionManager2
import os
from collections import defaultdict

app = Flask(__name__)

def get_application_volumes():
    CoInitialize()
    sessions = AudioUtilities.GetAllSessions()
    app_volumes_dict = defaultdict(lambda: {"instances": 0, "total_volume": 0, "can_pause": False, "icon": "static/icons/default.png"})

    for session in sessions:
        if session.Process and session.SimpleAudioVolume:
            process_name = session.Process.name()
            volume_level = int(session.SimpleAudioVolume.GetMasterVolume() * 100)
            can_pause = hasattr(session, 'Control') and session.Control is not None

            if os.path.exists(f"static/icons/{process_name}.png"):
                icon_path = f"static/icons/{process_name}.png"
            else:
                icon_path = "static/icons/default.png"

            app_data = app_volumes_dict[process_name]
            app_data["instances"] += 1
            app_data["total_volume"] += volume_level
            app_data["can_pause"] = app_data["can_pause"] or can_pause
            app_data["icon"] = icon_path

    # Convert to list with averaged volume
    app_volumes = [
        {
            "name": name,
            "volume": app_data["total_volume"] // app_data["instances"],
            "instances": app_data["instances"],
            "can_pause": app_data["can_pause"],
            "icon": app_data["icon"]
        }
        for name, app_data in app_volumes_dict.items()
    ]

    return app_volumes

def set_application_volume(app_name, volume_level):
    CoInitialize()
    sessions = AudioUtilities.GetAllSessions()
    found = False

    for session in sessions:
        if session.Process and session.SimpleAudioVolume:
            process_name = session.Process.name()
            if process_name.lower() == app_name.lower():
                session.SimpleAudioVolume.SetMasterVolume(int(volume_level) / 100, None)
                found = True

    if found:
        return {"message": f"Volume for all instances of {app_name} set to {volume_level}%"}
    else:
        return {"error": f"Application {app_name} not found!"}

def pause_application(app_name):
    CoInitialize()
    sessions = AudioUtilities.GetAllSessions()
    found = False

    for session in sessions:
        if session.Process and hasattr(session, 'Control') and session.Control:
            process_name = session.Process.name()
            if process_name.lower() == app_name.lower():
                session.Control.Stop()
                found = True

    if found:
        return {"message": f"Paused all instances of {app_name}"}
    else:
        return {"error": f"Application {app_name} cannot be paused or not found!"}

@app.route("/")
def index():
    return render_template("index.html", applications=get_application_volumes())

@app.route("/volumes", methods=["GET"])
def get_volumes():
    return jsonify(get_application_volumes())

@app.route("/set_volume", methods=["POST"])
def set_volume():
    if not request.is_json:
        return jsonify({"error": "Request must be in JSON format"}), 415

    data = request.get_json()
    app_name = data.get("app_name")
    volume = data.get("volume")

    if app_name and volume is not None:
        return jsonify(set_application_volume(app_name, volume))

    return jsonify({"error": "Invalid request data"}), 400

@app.route("/pause", methods=["POST"])
def pause():
    if not request.is_json:
        return jsonify({"error": "Request must be in JSON format"}), 415

    data = request.get_json()
    app_name = data.get("app_name")

    if app_name:
        return jsonify(pause_application(app_name))

    return jsonify({"error": "Invalid request data"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
