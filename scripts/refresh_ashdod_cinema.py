#!/usr/bin/env python3
"""Daily, city-scoped official cinema intake. Never discard metadata on source failure.

Public Cinema City CMS queries use the same anonymous visitor instance as its
website. No credentials, browser challenge solving, or private endpoints.
Official promotional poster URLs are validated and referenced remotely; no image is copied.
"""
import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode, urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'events-preview/ashdod/data/cinema.json'
QA = ROOT / 'events-preview/ashdod/data/cinema-refresh-status.json'
EDITORIAL = ROOT / 'events-preview/ashdod/data/cinema-editorial.json'
TZ = ZoneInfo('Asia/Jerusalem')
CITY = 'https://www.cinema-city.co.il'
HOT = 'https://hotcinema.co.il'
VENUES = {'cinema-city': 'סינמה סיטי אשדוד', 'hot-cinema': 'HOT Cinema אשדוד'}
TODAY = datetime.now(TZ).date().isoformat()
STAMP = datetime.now(TZ).isoformat(timespec='seconds')
CACHE = None
OVERRIDES = {}


def request(url, payload=None, headers=None):
    key = hashlib.sha256((url + json.dumps(payload, sort_keys=True)).encode()).hexdigest()
    path = CACHE / (key + '.txt') if CACHE else None
    if path and path.exists():
        return path.read_text(encoding='utf-8')
    base = {'User-Agent': 'ISNET cinema listings daily verification/1.0',
            'Accept-Language': 'he-IL,he;q=0.9'}
    base.update(headers or {})
    response = requests.request('POST' if payload is not None else 'GET', url,
                                json=payload, headers=base, timeout=30)
    response.raise_for_status()
    text = response.text
    if re.search(r'<title>[^<]*(?:Just a moment|Access Denied)|verify you are human', text, re.I):
        raise ValueError('Source requests human verification; intake stopped')
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    return text


def plain(text):
    return ' '.join(BeautifulSoup(text or '', 'html.parser').get_text(' ', strip=True).split())


def base_title(title):
    title = unicodedata.normalize('NFKC', title or '')
    title = re.sub(r'^(?:סינמה נוסטלגיה\s*[-–:]\s*|אופרה בשלייקס\s*[-–:]\s*)', '', title)
    title = re.split(r'\s*[-–]?\s*(?:מדובב|מתורגם|גרסה באנגלית|באנגלית|אנגלית\s*$|הקרנה רגישה)', title)[0]
    return re.sub(r'[^a-z0-9א-ת]', '', title.lower())


def youtube_id(url):
    match = re.search(r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=))([\w-]{11})(?:[^\w-]|$)', url or '')
    return match[1] if match else None


def publisher_kind(author):
    # Reviewed distributor, studio and creator identities; unknown channels are not official by default.
    official = {'unitedkingfilms', 'Tulip Entertainment', 'Amazon MGM Studios', 'סרטי נחשון',
        'ARIA אופרה בקולנוע', 'Lev Cinema', 'Red Cape רד קייפ', 'New Cinema - קולנוע חדש',
        'Shoval Film Production', 'Filmhouse. Israel', 'Disney Israel', 'Transfax Film Productions',
        'עמית אולמן - Amit Ulman', 'Intramovies', 'MarvelIsrael', 'סולטיז', 'Sony Pictures Entertainment',
        ' КиноРай- KinoRai- кино в Израиле на русском языке'}
    portals = {'סרט סרט - חדשות הקולנוע', 'אתר סרט', 'Rotten Tomatoes Classic Trailers'}
    return 'official_publisher' if author in official else 'cinema_portal' if author in portals else 'unverified_publisher'


def verify_trailer(row):
    override = OVERRIDES.get(base_title(row['title']))
    if override:
        row['trailer_url'] = override['url']
        row['trailer_source_override'] = override['source_url']
    vid = youtube_id(row.get('trailer_url'))
    if not vid:
        return row
    try:
        data = json.loads(request('https://www.youtube.com/oembed?' + urlencode({
            'url': 'https://www.youtube.com/watch?v=' + vid, 'format': 'json'})))
        if not re.search(r'/embed/' + re.escape(vid), data.get('html', '')):
            raise ValueError('No embeddable player returned')
        if override and data.get('author_name') != override['author']:
            raise ValueError('Official publisher identity changed')
        row['trailer_verified'] = {'youtube_id': vid, 'title': data.get('title'),
                                   'author': data.get('author_name'),
                                   'publisher_kind': publisher_kind(data.get('author_name')),
                                   'author_url': data.get('author_url'),
                                   'verified_at': STAMP, 'method': 'official cinema link + YouTube oEmbed'}
    except Exception as exc:
        row['trailer_error'] = str(exc)[:180]
    return row


def verify_poster(row):
    url = row.get('poster_source_url')
    if not url:
        return row
    try:
        with requests.get(url, timeout=20, stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                raise ValueError('Official poster URL did not return an image')
        row['poster_verified'] = {'url': url, 'source_url': row['source_url'],
            'verified_at': STAMP, 'content_type': content_type, 'delivery': 'remote_official_source'}
    except Exception as exc:
        row['poster_error'] = str(exc)[:180]
    return row


def city_query(token, collection, filter_):
    items, offset = [], 0
    while True:
        result = json.loads(request(CITY + '/_api/cloud-data/v1/wix-data/collections/query',
            {'collectionName': collection, 'dataQuery': {'filter': filter_,
             'paging': {'limit': 1000, 'offset': offset}}, 'options': {}},
            {'Authorization': token}))
        batch = result['items']
        items.extend(batch)
        total = int(result.get('totalCount', result.get('totalResults', len(items))))
        if len(items) >= total:
            return items
        if not batch or offset > 20000:
            raise ValueError('Incomplete CMS pagination')
        offset += len(batch)


def collect_city():
    # Anonymous public visitor token, never persisted into the dataset/report.
    tokens = json.loads(request(CITY + '/_api/v1/access-tokens'))
    token = tokens['apps']['675bbcef-18d8-41f5-800e-131ec9e08762']['instance']
    locations = city_query(token, 'CityDynamicPage', {'slug': 'ashdod', 'active': True})
    if len(locations) != 1 or locations[0]['hebrewName'] != VENUES['cinema-city']:
        raise ValueError('Ashdod branch identity could not be verified')
    location = locations[0]
    sessions = city_query(token, 'SyncPresentations', {'locationName': location['hebrewName'],
                         'soldout': False, 'businessDate': {'$gte': {'$date': TODAY + 'T00:00:00Z'}}})
    features = city_query(token, 'SyncFeatures', {})
    features = {str(x['externalId']): x for x in features}
    rows = {}
    for session in sessions:
        payload = session.get('payloadJson') or '{}'
        payload = json.loads(payload) if isinstance(payload, str) else payload
        if session.get('private') or payload.get('private'):
            continue
        if session.get('locationName') != location['hebrewName'] or int(payload.get('venueLocationId', 0)) != int(location['locationId']):
            raise ValueError('Non-Ashdod session in branch query')
        ident = str(int(session['featureId']))
        feature = features.get(ident, {})
        categories = feature.get('categoryName', [])
        if any(c == 'SHOW' for c in categories) or re.search(r'פודקאסט|סטנד.?אפ|קומדי בר', session['featureName']):
            continue
        dt = session.get('dateTime', '')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?', dt):
            raise ValueError('Unexpected source datetime representation')
        # The official website formats this wall-clock string directly; no UTC conversion.
        day, hour = dt[:10], dt[11:16]
        if day < TODAY:
            continue
        row = rows.setdefault(ident, {'source_id': ident, 'title': feature.get('name') or session['featureName'],
            'source_url': CITY + '/movie/' + ident, 'venue_id': 'cinema-city',
            'synopsis': plain(feature.get('synopsis')), 'genres': feature.get('genre') or [],
            'runtime_minutes': int(feature.get('duration') or payload.get('durationInMinutes') or 0) or None,
            'age_rating': feature.get('ratingName') or session.get('featureRatingName'),
            'poster_source_url': feature.get('imageSourceUrl') or feature.get('image'),
            'trailer_url': feature.get('trailer'), 'schedule': {}, 'sessions': []})
        row['schedule'].setdefault(day, set()).add(hour)
        row['sessions'].append({'date': day, 'time': hour, 'source_event_id': str(session['externalId']),
            'booking_url': 'https://tickets.cinema-city.co.il/order/' + str(session['externalId']),
            'screen': session.get('venueTypeName'), 'dubbed_language': payload.get('dubbedLanguageISO'),
            'subtitled_language': payload.get('subbedLanguageISO')})
    if not rows:
        raise ValueError('Empty official Ashdod listing; existing schedules retained for review')
    return list(rows.values())


def hot_detail(row):
    try:
        soup = BeautifulSoup(request(row['source_url']), 'html.parser')
        if not soup.h1 or base_title(soup.h1.get_text()) != base_title(row['title']):
            raise ValueError('Movie detail identity mismatch')
        desc = soup.select_one('.movie-description-mobile')
        if desc:
            row['synopsis'] = plain(str(desc))
        meta = [plain(str(x)) for x in soup.select('.desc-text')]
        for text in meta:
            runtime = re.fullmatch(r'(\d+) דקות', text)
            if runtime:
                row['runtime_minutes'] = int(runtime[1])
            elif 'הגבלת גיל:' in text:
                row['age_rating'] = text.split('הגבלת גיל:', 1)[1].strip()
        if meta:
            row['genres'] = [x.strip() for x in meta[0].split(',') if x.strip()]
        ids = []
        for tag in soup.select('iframe[src], a[href], [data-src], [data-url]'):
            for attr in ('src', 'href', 'data-src', 'data-url'):
                url = tag.get(attr, '')
                if youtube_id(url) and url not in ids:
                    ids.append(url)
        if ids:
            row['trailer_url'] = ids[0]
    except Exception as exc:
        row['metadata_error'] = str(exc)[:180]
    return row


def collect_hot():
    html = request(HOT + '/theater/5')
    match = re.search(r'app\.movies\s*=\s*(\[.*?\]);', html, re.S)
    theaters = re.search(r'app\.theaters\s*=\s*(\[.*?\]);', html, re.S)
    if not match or not theaters:
        raise ValueError('Official branch metadata unavailable')
    branches = json.loads(theaters[1])
    if not any(int(x.get('ID', 0)) == 5 and 'אשדוד' in x.get('Name', '') for x in branches):
        raise ValueError('HOT branch 5 is not confirmed as Ashdod')
    features = {int(x['ID']): x for x in json.loads(match[1])}
    url = HOT + '/tickets/TheaterEvents2?' + urlencode({'movieid': '', 'date': '',
        'theatreid': 5, 'site': '', 'time': '', 'type': '', 'lang': '', 'kinorai': '',
        'genreId': '', 'screentype': '', 'subdub': '', 'isnew': ''})
    groups = json.loads(request(url))['TheaterEvents']
    rows = {}
    for group in groups:
        ident = int(group['MovieId'])
        name = group['MovieName'].strip()
        if re.search(r'קומדי בר|סטנד.?אפ|פודקאסט|שרנו.*המסיבה', name):
            continue
        feature = features.get(ident, {})
        if not feature.get('PageUrl'):
            raise ValueError('Session movie missing from official catalog')
        for session in group.get('Dates', []):
            if int(session.get('TheaterId', 0)) != 5:
                raise ValueError('Non-Ashdod HOT session')
            date = session.get('Date', '')
            day, hour = date[:10], session.get('Hour')
            if day < TODAY:
                continue
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day) or not re.fullmatch(r'\d{2}:\d{2}', hour or '') or date[11:16] != hour:
                raise ValueError('Invalid HOT session datetime')
            row = rows.setdefault(ident, {'source_id': str(ident), 'title': name, 'venue_id': 'hot-cinema',
                'source_url': urljoin(HOT, feature['PageUrl']), 'schedule': {}, 'sessions': [],
                'poster_source_url': urljoin(HOT + '/images/', feature.get('Poster', '')),
                'synopsis': '', 'genres': []})
            row['schedule'].setdefault(day, set()).add(hour)
            row['sessions'].append({'date': day, 'time': hour, 'source_event_id': str(session['EventId']),
                'booking_url': HOT + '/order?' + urlencode({'theaterId': 5, 'eventId': session['EventId']}),
                'dubbed_language': session.get('DubbedLanguage'), 'subtitled_language': session.get('SubtitledLanguage'),
                'screen': group.get('ScreeningType')})
    if not rows:
        raise ValueError('Empty official HOT Ashdod listing; existing schedules retained for review')
    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(hot_detail, rows.values()))


def merge(existing, sources):
    movies = copy.deepcopy(existing.get('movies', []))
    lookup = {}
    for movie in movies:
        lookup.setdefault(base_title(movie['title']), []).append(movie)
    # Consolidate language variants, keeping old deep links as aliases.
    for candidates in lookup.values():
        primary = candidates[0]
        for other in candidates[1:]:
            primary.setdefault('aliases', []).append(other['id'])
            primary.setdefault('aliases', []).extend(other.get('aliases', []))
            for venue in other.get('venues', []):
                current = next((v for v in primary.get('venues', []) if v['id'] == venue['id']), None)
                if current is None:
                    primary.setdefault('venues', []).append(venue)
                else:
                    for day, times in venue.get('schedule', {}).items():
                        current.setdefault('schedule', {})[day] = sorted(set(current.get('schedule', {}).get(day, [])) | set(times))
                    current.setdefault('sessions', []).extend(venue.get('sessions', []))
            movies.remove(other)
    lookup = {base_title(m['title']): m for m in movies}
    for movie in movies:
        movie['title'] = re.split(r'\s*[-–]?\s*(?:מדובב|מתורגם|גרסה באנגלית|באנגלית|אנגלית\s*$|הקרנה רגישה)', movie['title'])[0].strip(' -–')
    for venue_id, result in sources.items():
        if result['status'] != 'ok':
            continue
        # Only successful complete official snapshots may replace this venue's schedules.
        for movie in movies:
            for venue in movie.get('venues', []):
                if venue['id'] == venue_id:
                    venue['schedule'] = {}
                    venue['sessions'] = []
                    venue['schedule_verified_at'] = STAMP
        for row in result['movies']:
            key = base_title(row['title'])
            movie = lookup.get(key)
            if not movie:
                movie = {'id': venue_id + '-' + row['source_id'], 'title': row['title'],
                         'synopsis': '', 'trailer_youtube_id': None, 'is_family': False, 'venues': []}
                lookup[key] = movie
                movies.append(movie)
                movie['title'] = re.split(r'\s*[-–]?\s*(?:מדובב|מתורגם|גרסה באנגלית|באנגלית|אנגלית\s*$|הקרנה רגישה)', movie['title'])[0].strip(' -–')
            movie.setdefault('source_movies', {})[venue_id + ':' + row['source_id']] = {
                'title': row['title'], 'url': row['source_url'], 'verified_at': STAMP}
            if row.get('synopsis') and not movie.get('synopsis'):
                # A short source-attributed synopsis; retain richer editorial text already verified.
                synopsis = re.split(r'(?<=[.!?])\s+', row['synopsis'].replace('\\n', ' '))
                movie['synopsis'] = ' '.join(synopsis[:2])[:600].rsplit(' ', 1)[0] if len(' '.join(synopsis[:2])) > 600 else ' '.join(synopsis[:2])
                movie['synopsis_source_url'] = row['source_url']
            for field in ('runtime_minutes', 'age_rating', 'genres'):
                if row.get(field) and not movie.get(field):
                    movie[field] = row[field]
                    movie.setdefault('metadata_sources', {})[field] = row['source_url']
            if 'אנימציה' in row.get('genres', []) or re.search(r'מדובב(?: לעברית)?$', row['title']):
                movie['is_family'] = True
            if row.get('poster_source_url'):
                movie.setdefault('poster_candidates', {})[venue_id] = {'url': row['poster_source_url'],
                    'source_url': row['source_url'], 'rights_status': 'reuse_permission_not_verified'}
            if row.get('poster_verified') and (venue_id == 'cinema-city' or not movie.get('poster_url')):
                movie['poster_url'] = row['poster_verified']['url']
                movie['poster_verification'] = row['poster_verified']
            if row.get('trailer_error'):
                movie['trailer_review_note'] = row['trailer_error']
            trailer = row.get('trailer_verified')
            if trailer and (row.get('trailer_source_override') or not movie.get('trailer_youtube_id') or movie.get('trailer_youtube_id') == trailer['youtube_id']):
                movie['trailer_youtube_id'] = trailer['youtube_id']
                movie['trailer_url'] = 'https://www.youtube.com/watch?v=' + trailer['youtube_id']
                movie['trailer_source_url'] = row.get('trailer_source_override') or row['source_url']
                movie['trailer_source_name'] = VENUES[venue_id] + ' — official movie source'
                movie['trailer_verification'] = trailer
            elif row.get('trailer_url') and not movie.get('trailer_youtube_id'):
                movie['trailer_page_url'] = row['source_url']
            venue = next((v for v in movie['venues'] if v['id'] == venue_id), None)
            if venue is None:
                venue = {'id': venue_id, 'name': VENUES[venue_id], 'schedule': {}, 'sessions': []}
                movie['venues'].append(venue)
            venue['article_url'] = row['source_url']
            venue['schedule_source_url'] = CITY + '/city/ashdod' if venue_id == 'cinema-city' else HOT + '/theater/5'
            venue['schedule_verified_at'] = STAMP
            venue['source_branch_id'] = 1181 if venue_id == 'cinema-city' else 5
            for day, times in row['schedule'].items():
                venue['schedule'][day] = sorted(set(venue['schedule'].get(day, [])) | set(times))
            venue['sessions'].extend(row['sessions'])
    existing['movies'] = movies
    existing['updated_at'] = STAMP
    existing['source_name'] = 'סינמה סיטי ו־HOT Cinema — הקרנות מאומתות באשדוד'
    existing['source_url'] = CITY + '/city/ashdod'
    existing['sources'] = [{'id': key, 'name': VENUES[key],
        'url': CITY + '/city/ashdod' if key == 'cinema-city' else HOT + '/theater/5',
        'status': result['status'], 'checked_at': STAMP} for key,result in sources.items()]
    existing['refresh_policy'] = {'timezone': 'Asia/Jerusalem', 'schedule_utc': '15 5 * * *',
        'failure_behavior': 'retain previously verified metadata and schedules; expired dates are hidden',
        'poster_policy': 'reference verified official promotional image URLs remotely; retain source attribution'}
    active = [m for m in movies if any(any(d >= TODAY and t for d, t in v.get('schedule', {}).items()) for v in m['venues'])]
    existing['stats'] = {'movie_cards': len(active), 'family_movie_cards': sum(bool(m.get('is_family')) for m in active),
        'cinema_city_movies': sum(any(v['id'] == 'cinema-city' and any(d >= TODAY and t for d,t in v.get('schedule',{}).items()) for v in m['venues']) for m in active),
        'hot_cinema_movies': sum(any(v['id'] == 'hot-cinema' and any(d >= TODAY and t for d,t in v.get('schedule',{}).items()) for v in m['venues']) for m in active)}
    report = {'checked_at': STAMP, 'city': 'אשדוד', 'sources': {k: {f:v for f,v in r.items() if f != 'movies'} for k,r in sources.items()},
        'counts': {'active_movies': len(active), 'synopsis': sum(bool(m.get('synopsis')) for m in active),
            'official_poster': sum(bool(m.get('poster_url') and m.get('poster_verification')) for m in active),
            'trailer': sum(bool(m.get('trailer_youtube_id')) for m in active),
            'verified_trailer': sum(bool(m.get('trailer_youtube_id')) for m in active),
            'official_publisher_trailer': sum(bool(m.get('trailer_youtube_id') and m.get('trailer_verification',{}).get('publisher_kind') == 'official_publisher') for m in active),
            'verified_showtimes': sum(any(v.get('schedule_verified_at') and any(d >= TODAY and t for d,t in v.get('schedule',{}).items()) for v in m['venues']) for m in active),
            'runtime': sum(bool(m.get('runtime_minutes')) for m in active), 'age_rating': sum(bool(m.get('age_rating')) for m in active)},
        'missing': [{'id': m['id'], 'title': m['title'], 'fields': [f for f in ('synopsis','genres','runtime_minutes','poster_url','trailer_youtube_id') if not m.get(f)]} for m in active if any(not m.get(f) for f in ('synopsis','genres','runtime_minutes','poster_url','trailer_youtube_id'))],
        'poster_note': 'Official promotional images referenced remotely after image URL validation; no rights ownership is asserted.'}
    return existing, report


def main():
    global CACHE, OVERRIDES
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache-dir', type=Path, help='Local research cache; omit for every scheduled fresh intake')
    args = parser.parse_args()
    CACHE = args.cache_dir
    editorial = json.loads(EDITORIAL.read_text(encoding='utf-8')) if EDITORIAL.exists() else {}
    OVERRIDES = {base_title(k): v for k,v in editorial.get('trailer_overrides', {}).items()}
    original = json.loads(DATA.read_text(encoding='utf-8'))
    sources = {}
    for key, collector in [('cinema-city', collect_city), ('hot-cinema', collect_hot)]:
        try:
            rows = collector()
            excluded = [{'title': r['title'], 'reason': 'Official description identifies a stage/storytelling event'} for r in rows
                        if re.search(r'שעת סיפור תיאטרלית|מופע סטנד.?אפ|הצגת ילדים', r.get('synopsis', ''))]
            rows = [r for r in rows if r['title'] not in {e['title'] for e in excluded}]
            previous = sum(any(v['id'] == key and any(d >= TODAY and times for d,times in v.get('schedule', {}).items())
                               for v in m.get('venues', [])) for m in original.get('movies', []))
            observed = len({base_title(r['title']) for r in rows})
            if previous >= 10 and observed < previous * .35:
                raise ValueError(f'Suspicious listing drop ({previous} to {observed}); preserve verified data for review')
            # A shared video assigned to unrelated film titles is not a verified film trailer.
            ids = {}
            for row in rows:
                vid = youtube_id(row.get('trailer_url'))
                if vid:
                    ids.setdefault(vid, set()).add(base_title(row['title']))
            for row in rows:
                if len(ids.get(youtube_id(row.get('trailer_url')), set())) > 1:
                    row['trailer_error'] = 'Same video linked to unrelated movies; needs editorial verification'
                    row['trailer_url'] = None
            with ThreadPoolExecutor(max_workers=3) as pool:
                rows = list(pool.map(verify_trailer, rows))
                rows = list(pool.map(verify_poster, rows))
            sources[key] = {'status': 'ok', 'movies': rows, 'movie_variants': len(rows),
                'excluded_non_films': excluded,
                'sessions': sum(len(r['sessions']) for r in rows),
                'metadata_errors': [{'title': r['title'], 'error': r['metadata_error']} for r in rows if r.get('metadata_error')],
                'trailer_errors': [{'title': r['title'], 'error': r['trailer_error']} for r in rows if r.get('trailer_error')]}
            print(key, len(rows), 'movie variants; verified sessions', sources[key]['sessions'], flush=True)
        except Exception as exc:
            sources[key] = {'status': 'failed', 'error': str(exc)[:250]}
            print(key, 'failed:', exc, flush=True)
    existing = json.loads(DATA.read_text(encoding='utf-8'))
    for movie in existing.get('movies', []):
        synopsis = editorial.get('synopses', {}).get(movie['id'])
        if synopsis:
            movie['synopsis'] = synopsis
            movie['synopsis_editorial'] = True
    if not any(r['status'] == 'ok' for r in sources.values()):
        QA.write_text(json.dumps({'checked_at': STAMP, 'sources': sources, 'data_preserved': True}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return 1
    updated, report = merge(existing, sources)
    DATA.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    QA.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['counts'], ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
