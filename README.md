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
    - Add the scope: `.../auth/gmail.modify` and `.../auth/gmail.readonly`.
4.  **Create Credentials**:
    - Go to **Credentials** > **Create Credentials** > **OAuth client ID**.
    - Select **Web application** as the application type.
    - **Authorized redirect URIs**: Add `http://127.0.0.1:5000/auth/google/callback` (and `http://localhost:5000/auth/google/callback`).
5.  **Get Secrets**: Copy the **Client ID** and **Client Secret**. These go into your backend `.env` file.

### 2. Backend Setup
1. `cd backend`
2. Create a `.env` file from the template (`.env.example`):
   ```env
   FLASK_SECRET_KEY=any_random_string
   GOOGLE_CLIENT_ID=your_client_id_from_step_1
   GOOGLE_CLIENT_SECRET=your_client_secret_from_step_1
   FRONTEND_URL=http://localhost:5173
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python app.py`

### 3. Frontend Setup
1. `cd frontend`
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`

## Troubleshooting

### "Invalid State Parameter"
If you encounter this error during login, ensure:
1.  **Consistent Hostname**: Access the application via `http://localhost:5173` consistently. Do not mix `localhost` and `127.0.0.1` as cookies (sessions) are host-specific.
2.  **Redirect URIs**: Ensure both `http://localhost:5000/auth/google/callback` and `http://127.0.0.1:5000/auth/google/callback` are added to your Google Cloud Console.
3.  **Refresh**: Sometimes an old session cookie causes issues. Try clearing your browser cookies for `localhost` or opening in an Incognito window.

## Deployment

### Backend (Render)
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `gunicorn -k eventlet -w 1 --chdir backend app:app`
- **Environment Variables**: Set `FLASK_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `FRONTEND_URL`.

### Frontend (Netlify)
- **Build Command**: `npm run build`
- **Publish Directory**: `frontend/dist`
- **Environment Variables**: Set `VITE_API_URL` to your Render backend URL.

## Security & Privacy
- **Stateless**: All data is stored in volatile memory and cleared on logout or session expiry (30 mins).
- **Safety**: Deletion actions move emails to **Trash**; they are not permanently deleted immediately.
