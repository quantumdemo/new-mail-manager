import re
from collections import defaultdict

def analyze_emails(emails):
    senders = defaultdict(lambda: {'count': 0, 'total_size': 0, 'emails': [], 'domain': ''})
    total_estimated_size = 0
    for email in emails:
        sender_full = email['sender']
        match = re.search(r'<(.*)>', sender_full)
        addr = match.group(1) if match else sender_full
        s = senders[addr]
        s['count'] += 1; s['total_size'] += email['size']; s['emails'].append(email); s['domain'] = addr.split('@')[-1] if '@' in addr else ''
        total_estimated_size += email['size']
    results = []
    for addr, data in senders.items():
        cat = 'newsletter' if any(k in addr.lower() for k in ['news', 'promo', 'no-reply', 'update']) else 'bulk' if data['count'] > 20 else 'regular'
        rec = 'safe' if cat == 'newsletter' else 'review' if cat == 'bulk' or data['total_size'] > 5*1024*1024 else 'keep'
        expl = "Promotional sender identified by address pattern." if rec == 'safe' else "High volume sender." if cat == 'bulk' else "Large total size." if data['total_size'] > 5*1024*1024 else "Regular correspondence."
        results.append({'sender': addr, 'domain': data['domain'], 'count': data['count'], 'total_size': data['total_size'], 'category': cat, 'recommendation': rec, 'confidence': 0.9 if rec != 'keep' else 0.5, 'explanation': expl, 'sample_emails': data['emails'][:3]})
    results.sort(key=lambda x: x['total_size'], reverse=True)
    return {'total_scanned': len(emails), 'total_estimated_size': total_estimated_size, 'senders': results}
