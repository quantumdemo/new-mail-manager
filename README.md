# Mail Manager

Privacy-first, stateless web application to analyze and clean your Gmail inbox.

## Features
- **Secure Google OAuth**: Connect your Gmail account safely.
- **Stateless**: No database, no persistent storage of tokens.
- **AI Analysis**: Smart grouping and recommendations.
- **Quick Clean**: One-click cleanup for safe-to-delete emails.
- **PWA**: Installable on mobile and desktop.

## Setup Guide

### 1. Google OAuth Configuration
To use this application, you must set up a project in the Google Cloud Console:

1.  **Create a Project**: Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2.  **Enable Gmail API**: Search for "Gmail API" in the library and click **Enable**.
3.  **Configure OAuth Consent Screen**:
    - Choose **External** user type.
    - Add the scopes: `.../auth/gmail.modify` and `.../auth/gmail.readonly`.
4.  **Create Credentials**:
    - Go to **Credentials** > **Create Credentials** > **OAuth client ID**.
    - Select **Web application** as the application type.
    - **Authorized redirect URIs**: Add `http://127.0.0.1:5000/auth/google/callback` and/or `http://localhost:5000/auth/google/callback`.
5.  **Get Secrets**: Copy the **Client ID** and **Client Secret**.

### 2. Backend Setup
1. `cd backend`
2. Create a `.env` file from `.env.example`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python app.py`

### 3. Frontend Setup
1. `cd frontend`
2. Install dependencies: `npm install`
3. Run: `npm run dev`

## Troubleshooting

### "Invalid State Parameter"
This error occurs if the session cookie is missing or mismatched during the OAuth callback.
1.  **Consistent Hostname**: Always use `http://127.0.0.1:5173` instead of `localhost` in your browser if you face issues. Cookies are hostname-bound.
2.  **Browser Settings**: Ensure your browser is not blocking "Third-party cookies" or cookies from `localhost`/`127.0.0.1`.
3.  **Clear Cookies**: If you recently changed environment variables, clear your cookies for the site and try again.

## Deployment
- **Backend (Render)**: Use `gunicorn -k eventlet -w 1 --chdir backend app:app`.
- **Frontend (Netlify)**: Publish the `dist` folder. Ensure `VITE_API_URL` is set to your backend.

## Security
- **Stateless**: Sessions are memory-only and expire after 30 minutes of inactivity.
- **Safety**: "Delete" actions move emails to **Trash** for user safety.
