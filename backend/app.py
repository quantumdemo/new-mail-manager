import os
import datetime
import threading
import time
from flask import Flask, request, jsonify, session, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
from auth import get_google_flow
from email_service import EmailService
from analysis import analyze_emails

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

# Security Refinements
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(minutes=30)
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
CORS(app, supports_credentials=True, origins=[FRONTEND_URL])
socketio = SocketIO(app, cors_allowed_origins=FRONTEND_URL)

# In-memory session store with cleanup
user_sessions = {}
session_lock = threading.Lock()

def cleanup_sessions():
    while True:
        time.sleep(600)
        now = time.time()
        with session_lock:
            to_delete = [sid for sid, data in user_sessions.items() if now - data.get('created_at', 0) > 3600]
            for sid in to_delete:
                del user_sessions[sid]

threading.Thread(target=cleanup_sessions, daemon=True).start()

@app.route('/auth/google/login')
def google_login():
    flow = get_google_flow(url_for('google_callback', _external=True))
    auth_url, state = flow.authorization_url()
    session['google_state'] = state
    return jsonify({'url': auth_url})

@app.route('/auth/google/callback')
def google_callback():
    # Verify state to prevent CSRF
    if request.args.get('state') != session.get('google_state'):
        return "Invalid state parameter", 400

    flow = get_google_flow(url_for('google_callback', _external=True))
    flow.fetch_token(authorization_response=request.url)

    sid = os.urandom(16).hex()
    c = flow.credentials
    with session_lock:
        user_sessions[sid] = {
            'created_at': time.time(),
            'credentials': {
                'token': c.token,
                'refresh_token': c.refresh_token,
                'token_uri': c.token_uri,
                'client_id': c.client_id,
                'client_secret': c.client_secret,
                'scopes': c.scopes
            }
        }
    return f"<script>window.opener.postMessage({{type:'AUTH_SUCCESS',session_id:'{sid}'}}, '{FRONTEND_URL}');window.close();</script>"

@app.route('/api/scan', methods=['POST'])
def scan():
    sid = request.json.get('session_id')
    with session_lock:
        ud = user_sessions.get(sid)
    if not ud: return "Unauthorized", 401
    service = EmailService(ud['credentials'], lambda c, t: socketio.emit('scan_progress', {'current': c, 'total': t}, room=sid))
    res = analyze_emails(service.fetch_emails(1000))
    ud['analysis'] = res
    return jsonify(res)

@app.route('/api/delete', methods=['POST'])
def delete():
    sid = request.json.get('session_id')
    with session_lock:
        ud = user_sessions.get(sid)
    if not ud: return "Unauthorized", 401
    EmailService(ud['credentials']).delete_emails(request.json.get('email_ids', []))
    return jsonify({'success': True})

@app.route('/auth/logout', methods=['POST'])
def logout():
    sid = request.json.get('session_id')
    with session_lock:
        if sid in user_sessions: del user_sessions[sid]
    session.clear()
    return jsonify({'success': True})

@socketio.on('join')
def on_join(data):
    from flask_socketio import join_room
    join_room(data.get('session_id'))

if __name__ == '__main__':
    socketio.run(app, debug=False, port=5000)
