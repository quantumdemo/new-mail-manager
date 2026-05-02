import os, datetime
from flask import Flask, request, jsonify, session, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
from auth import get_google_flow, get_ms_auth_url, acquire_ms_token
from email_service import EmailService
from analysis import analyze_emails

load_dotenv()
app = Flask(__name__); app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=datetime.timedelta(minutes=30))
CORS(app, supports_credentials=True); socketio = SocketIO(app, cors_allowed_origins="*")
user_sessions = {}

@app.route('/auth/google/login')
def google_login():
    flow = get_google_flow(url_for('google_callback', _external=True))
    auth_url, state = flow.authorization_url()
    session['google_state'] = state
    return jsonify({'url': auth_url})

@app.route('/auth/google/callback')
def google_callback():
    flow = get_google_flow(url_for('google_callback', _external=True))
    flow.fetch_token(authorization_response=request.url)
    sid = os.urandom(16).hex(); c = flow.credentials
    user_sessions[sid] = {'provider': 'gmail', 'credentials': {'token': c.token, 'refresh_token': c.refresh_token, 'token_uri': c.token_uri, 'client_id': c.client_id, 'client_secret': c.client_secret, 'scopes': c.scopes}}
    return f"<script>window.opener.postMessage({{type:'AUTH_SUCCESS',session_id:'{sid}'}},'*');window.close();</script>"

@app.route('/auth/outlook/login')
def outlook_login(): return jsonify({'url': get_ms_auth_url(url_for('outlook_callback', _external=True))})

@app.route('/auth/outlook/callback')
def outlook_callback():
    res = acquire_ms_token(request.args.get('code'), url_for('outlook_callback', _external=True))
    if "access_token" in res:
        sid = os.urandom(16).hex(); user_sessions[sid] = {'provider': 'outlook', 'credentials': res}
        return f"<script>window.opener.postMessage({{type:'AUTH_SUCCESS',session_id:'{sid}'}},'*');window.close();</script>"
    return "Auth Failed", 400

@app.route('/api/scan', methods=['POST'])
def scan():
    sid = request.json.get('session_id'); ud = user_sessions.get(sid)
    if not ud: return "Unauthorized", 401
    service = EmailService(ud['provider'], ud['credentials'], lambda c, t: socketio.emit('scan_progress', {'current': c, 'total': t}, room=sid))
    res = analyze_emails(service.fetch_emails(1000)); ud['analysis'] = res
    return jsonify(res)

@app.route('/api/delete', methods=['POST'])
def delete():
    sid = request.json.get('session_id'); ud = user_sessions.get(sid)
    if not ud: return "Unauthorized", 401
    EmailService(ud['provider'], ud['credentials']).delete_emails(request.json.get('email_ids', []))
    return jsonify({'success': True})

@app.route('/auth/logout', methods=['POST'])
def logout():
    sid = request.json.get('session_id')
    if sid in user_sessions: del user_sessions[sid]
    session.clear(); return jsonify({'success': True})

@socketio.on('join')
def on_join(data):
    from flask_socketio import join_room; join_room(data.get('session_id'))

if __name__ == '__main__': socketio.run(app, debug=False, port=5000)
