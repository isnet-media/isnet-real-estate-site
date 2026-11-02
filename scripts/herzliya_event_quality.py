"""Reviewed production types from exact organizer pages; never infer from site navigation."""
from urllib.parse import urlsplit,unquote

REVIEWED={
 ('friends-hist.co.il','/show/זוגות-בזיג-זג-קומדיה-בקצב-גבוה'):('theatre','theatre'),
 ('friends-hist.co.il','/show/עפרה-תיאטרון-העברי'):('theatre','theatre'),
 ('heichalbair.co.il','/מעשה_בחמישה_בלונים_-_שעת_סיפור_תיאטרלית_לקטנטנים'):('kids','story-time'),
}

def reviewed(event):
    source=event.get('source_url','')
    parsed=urlsplit(source)
    key=(parsed.hostname.removeprefix('www.') if parsed.hostname else '',unquote(parsed.path).rstrip('/').lower())
    target=REVIEWED.get(key)
    if not target:return event
    result={**event,'category':target[0],'subcategory':target[1],
            'classification_review':{'source_url':source,'checked_at':'2026-11-02','reason':'Organizer identifies a stage production, not a film screening'}}
    if target[0]=='kids':result['audiences']=sorted(set(result.get('audiences',[])+['kids']))
    return result
