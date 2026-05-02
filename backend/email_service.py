import os
import time
import datetime
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class EmailService:
    def __init__(self, credentials, progress_callback=None):
        self.credentials = credentials
        self.progress_callback = progress_callback

    def _report_progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def _get_service(self):
        creds = Credentials(**self.credentials)
        return build('gmail', 'v1', credentials=creds)

    def fetch_emails(self, max_results=1000, time_range_days=180):
        service = self._get_service()
        emails = []
        page_token = None

        date_cutoff = (datetime.datetime.now() - datetime.timedelta(days=time_range_days)).strftime('%Y/%m/%d')
        query = f'after:{date_cutoff}'

        while len(emails) < max_results:
            try:
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(100, max_results - len(emails)),
                    pageToken=page_token
                ).execute()

                messages = results.get('messages', [])
                if not messages:
                    break

                # Batch get metadata
                batch = service.new_batch_http_request()
                batch_results = []

                def callback(request_id, response, exception):
                    if exception is None:
                        batch_results.append(response)

                for msg in messages:
                    batch.add(service.users().messages().get(userId='me', id=msg['id'], format='metadata'), callback=callback)

                batch.execute()

                for m in batch_results:
                    headers = m.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                    date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

                    emails.append({
                        'id': m['id'],
                        'subject': subject,
                        'sender': sender,
                        'size': int(m.get('sizeEstimate', 0)),
                        'snippet': m.get('snippet', ''),
                        'date': date
                    })
                    self._report_progress(len(emails), max_results)
                    if len(emails) >= max_results:
                        break

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            except Exception as e:
                # Basic backoff if rate limited
                if "rateLimitExceeded" in str(e):
                    time.sleep(2)
                    continue
                break

        return emails

    def delete_emails(self, email_ids):
        service = self._get_service()
        # Batch delete (trash)
        # Gmail batch trash is not directly available via one call for individual IDs
        # in the same way, but we can batch the requests.
        for i in range(0, len(email_ids), 50):
            batch = service.new_batch_http_request()
            chunk = email_ids[i:i+50]
            for eid in chunk:
                batch.add(service.users().messages().trash(userId='me', id=eid))
            batch.execute()
            time.sleep(0.1) # Slight pause between batches
        return True
