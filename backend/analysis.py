import re
from collections import defaultdict

def analyze_emails(emails):
    """
    Analyzes a list of email metadata and groups them by sender/domain.
    Returns statistics and recommendations.
    """
    senders = defaultdict(lambda: {
        'count': 0,
        'total_size': 0,
        'all_ids': [],
        'emails_metadata': [],
        'domain': ''
    })

    total_estimated_size = 0
    for email in emails:
        sender_full = email['sender']
        match = re.search(r'<(.*)>', sender_full)
        addr = match.group(1) if match else sender_full

        s = senders[addr]
        s['count'] += 1
        s['total_size'] += email['size']
        s['all_ids'].append(email['id'])
        # Store metadata for preview (only first 3)
        if len(s['emails_metadata']) < 3:
            s['emails_metadata'].append({
                'id': email['id'],
                'subject': email['subject'],
                'date': email['date'],
                'size': email['size'],
                'snippet': email.get('snippet', '')
            })
        s['domain'] = addr.split('@')[-1] if '@' in addr else ''
        total_estimated_size += email['size']

    results = []
    for addr, data in senders.items():
        # Category heuristics
        is_promo = any(k in addr.lower() for k in ['news', 'promo', 'no-reply', 'update', 'marketing', 'info'])
        cat = 'newsletter' if is_promo else 'bulk' if data['count'] > 20 else 'regular'

        # Recommendation logic
        if cat == 'newsletter':
            rec = 'safe'
            expl = "Promotional sender identified by address pattern."
            conf = 0.95
        elif cat == 'bulk' or data['total_size'] > 5 * 1024 * 1024:
            rec = 'review'
            expl = "High volume or large total size. Review before cleaning."
            conf = 0.8
        else:
            rec = 'keep'
            expl = "Regular correspondence."
            conf = 0.5

        results.append({
            'sender': addr,
            'domain': data['domain'],
            'count': data['count'],
            'total_size': data['total_size'],
            'category': cat,
            'recommendation': rec,
            'confidence': conf,
            'explanation': expl,
            'all_ids': data['all_ids'],
            'sample_emails': data['emails_metadata']
        })

    results.sort(key=lambda x: x['total_size'], reverse=True)

    return {
        'total_scanned': len(emails),
        'total_estimated_size': total_estimated_size,
        'senders': results
    }
