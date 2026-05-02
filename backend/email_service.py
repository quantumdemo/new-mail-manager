import os
import requests
import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class EmailService:
    def __init__(self, provider, credentials, progress_callback=None):
        self.provider = provider
        self.credentials = credentials
        self.progress_callback = progress_callback

    def _report_progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def _request_with_retry(self, method, url, **kwargs):
        max_retries = 3
        backoff = 1
        for i in range(max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                if response.status_code == 429:
                    time.sleep(backoff); backoff *= 2; continue
                return response
            except Exception:
                time.sleep(backoff); backoff *= 2
        return None

    def fetch_emails(self, max_results=1000, time_range_days=180):
        if self.provider == 'gmail': return self._fetch_gmail(max_results, time_range_days)
        if self.provider == 'outlook': return self._fetch_outlook(max_results, time_range_days)
        return []

    def _fetch_gmail(self, max_results, time_range_days):
        creds = Credentials(**self.credentials)
        service = build('gmail', 'v1', credentials=creds)
        emails = []; page_token = None
        import datetime
        date_cutoff = (datetime.datetime.now() - datetime.timedelta(days=time_range_days)).strftime('%Y/%m/%d')
        query = f'after:{date_cutoff}'
        while len(emails) < max_results:
            results = service.users().messages().list(userId='me', q=query, maxResults=100, pageToken=page_token).execute()
            messages = results.get('messages', [])
            if not messages: break
            for msg in messages:
                m = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                headers = m.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                emails.append({'id': m['id'], 'subject': subject, 'sender': sender, 'size': int(m.get('sizeEstimate', 0)), 'snippet': m.get('snippet', ''), 'date': next((h['value'] for h in headers if h['name'].lower() == 'date'), '')})
                self._report_progress(len(emails), max_results)
                if len(emails) >= max_results: break
            page_token = results.get('nextPageToken')
            if not page_token: break
        return emails

    def _fetch_outlook(self, max_results, time_range_days):
        headers = {'Authorization': f"Bearer {self.credentials.get('access_token')}"}
        emails = []; import datetime
        date_cutoff = (datetime.datetime.now() - datetime.timedelta(days=time_range_days)).isoformat() + "Z"
        url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {date_cutoff}&$top=50"
        while url and len(emails) < max_results:
            resp = self._request_with_retry('GET', url, headers=headers)
            if not resp or resp.status_code != 200: break
            data = resp.json(); messages = data.get('value', [])
            for m in messages:
                emails.append({'id': m['id'], 'subject': m.get('subject'), 'sender': m.get('from', {}).get('emailAddress', {}).get('address'), 'size': int(m.get('size', 0)), 'date': m.get('receivedDateTime')})
                self._report_progress(len(emails), max_results)
                if len(emails) >= max_results: break
            url = data.get('@odata.nextLink')
        return emails

    def delete_emails(self, email_ids):
        if self.provider == 'gmail':
            creds = Credentials(**self.credentials)
            service = build('gmail', 'v1', credentials=creds)
            for eid in email_ids: service.users().messages().trash(userId='me', id=eid).execute()
        elif self.provider == 'outlook':
            headers = {'Authorization': f"Bearer {self.credentials.get('access_token')}"}
            for eid in email_ids: self._request_with_retry('POST', f"https://graph.microsoft.com/v1.0/me/messages/{eid}/move", headers=headers, json={"destinationId": "deleteditems"})
        return True
