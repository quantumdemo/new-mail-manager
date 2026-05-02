# Mail Manager

Privacy-first, stateless web application to analyze and clean your email inbox.

## Features
- **Secure OAuth**: Gmail & Outlook support.
- **Stateless**: No database, no persistent storage of tokens.
- **AI Analysis**: Smart grouping and recommendations.
- **Quick Clean**: One-click cleanup for safe-to-delete emails.
- **PWA**: Installable on mobile and desktop.

## Setup
### Backend
1. `cd backend && pip install -r requirements.txt`
2. Configure `.env` with Google/MS credentials.
3. `python app.py`

### Frontend
1. `cd frontend && npm install && npm run dev`

## Deployment
### Render (Backend)
- Build: `pip install -r backend/requirements.txt`
- Start: `gunicorn -k eventlet -w 1 --chdir backend app:app`
- Set `PYTHON_VERSION=3.11` and environment variables.

### Netlify (Frontend)
- Build: `npm run build`
- Dir: `frontend/dist`
- Create `frontend/public/_redirects`: `/* /index.html 200`

## Security
- Tokens kept only in-memory.
- Session expires after 30 mins.
- HTTPS required for production.
