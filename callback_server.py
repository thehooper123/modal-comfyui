"""
n8n Callback Server
Receives completed videos from n8n workflow and notifies the main app.
Run on port 5000: python callback_server.py
"""

import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# In-memory storage for callbacks (use Redis in production)
PENDING_CALLBACKS = {}


def register_callback(session_id, callback_url):
    """Register a callback to be notified when video is ready"""
    PENDING_CALLBACKS[session_id] = {
        "callback_url": callback_url,
        "created_at": datetime.now().isoformat(),
        "status": "waiting",
    }
    logger.info(f"Registered callback for session {session_id}")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route("/n8n-callback", methods=["POST"])
def n8n_callback():
    """
    Receive completed video from n8n workflow
    Expected payload:
    {
        "sessionId": "20240101_120000",
        "finalVideoUrl": "https://..../video.mp4",
        "georgeJson": {...},
        "bellaResponse": "..."
    }
    """
    try:
        data = request.get_json()
        session_id = data.get("sessionId")
        final_video_url = data.get("finalVideoUrl")
        george_json = data.get("georgeJson", {})
        
        if not session_id or not final_video_url:
            return (
                jsonify({"error": "Missing sessionId or finalVideoUrl"}),
                400,
            )
        
        logger.info(f"Received callback for session {session_id}")
        logger.info(f"Video URL: {final_video_url}")
        
        # Notify the main app (via its callback registration)
        if session_id in PENDING_CALLBACKS:
            callback_info = PENDING_CALLBACKS[session_id]
            
            # Call the registered callback URL if provided
            if callback_info.get("callback_url"):
                try:
                    resp = requests.post(
                        callback_info["callback_url"],
                        json={
                            "sessionId": session_id,
                            "finalVideoUrl": final_video_url,
                            "georgeJson": george_json,
                        },
                        timeout=30,
                    )
                    logger.info(f"Notified callback handler: {resp.status_code}")
                except Exception as e:
                    logger.error(f"Failed to notify callback: {e}")
            
            # Update status
            PENDING_CALLBACKS[session_id]["status"] = "completed"
            PENDING_CALLBACKS[session_id]["final_video_url"] = final_video_url
            
            return (
                jsonify({
                    "status": "received",
                    "message": f"Video for session {session_id} received successfully",
                }),
                200,
            )
        else:
            logger.warning(f"No callback registered for session {session_id}")
            return (
                jsonify({"warning": f"No callback for session {session_id}"}),
                202,
            )
    
    except Exception as e:
        logger.error(f"Error processing callback: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/register-callback", methods=["POST"])
def register_callback_endpoint():
    """
    Register a callback for a session
    Payload:
    {
        "sessionId": "20240101_120000",
        "callbackUrl": "http://localhost:5001/video-ready"
    }
    """
    try:
        data = request.get_json()
        session_id = data.get("sessionId")
        callback_url = data.get("callbackUrl")
        
        if not session_id or not callback_url:
            return (
                jsonify({"error": "Missing sessionId or callbackUrl"}),
                400,
            )
        
        register_callback(session_id, callback_url)
        
        return (
            jsonify({
                "status": "registered",
                "sessionId": session_id,
                "message": f"Callback registered for session {session_id}",
            }),
            200,
        )
    
    except Exception as e:
        logger.error(f"Error registering callback: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/callback-status/<session_id>", methods=["GET"])
def callback_status(session_id):
    """Check status of a callback"""
    if session_id in PENDING_CALLBACKS:
        return jsonify(PENDING_CALLBACKS[session_id]), 200
    else:
        return jsonify({"error": f"No callback for session {session_id}"}), 404


@app.route("/pending-callbacks", methods=["GET"])
def pending_callbacks():
    """Get all pending callbacks (for debugging)"""
    return (
        jsonify({
            "pending": len(PENDING_CALLBACKS),
            "callbacks": {
                sid: {
                    "status": cb["status"],
                    "created_at": cb["created_at"],
                }
                for sid, cb in PENDING_CALLBACKS.items()
            },
        }),
        200,
    )


if __name__ == "__main__":
    logger.info("Starting n8n Callback Server on port 5000")
    logger.info("Main app will connect to this server for video delivery")
    app.run(host="0.0.0.0", port=5000, debug=True)
