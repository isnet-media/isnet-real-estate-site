#!/usr/bin/env python3
"""Refresh the club hub from exact IFA source URLs; preserve failed records."""
import concurrent.futures, copy, json, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'sports/ashdod'
NOW = datetime.now(timezone.utc).isoformat()
ERRORS = []

def text(e):
    return e.get_text(' ', strip=True) if e else ''

def ident(u, key='player_id'):
    return parse_qs(urlparse(u).query).get(key, [''])[0]

def fetch(u):
    if urlparse(u).hostname != 'www.football.org.il':
        raise ValueError('Unexpected source host')
    with urllib.request.urlopen(u, timeout=25) as response:
        raw = response.read().decode('utf-8-sig')
    if raw.lstrip().startswith('<?xml'):
        root = ET.fromstring(raw)
        raw = next((e.text for e in root.iter() if e.tag.endswith('HtmlData')), '') or ''
    soup = BeautifulSoup(raw, 'html.parser')
    for node in soup.select('.sr-only,script,style'):
        node.decompose()
    return soup

def views(s, u):
    result = []
    for view in s.select('.table_view'):
        headers = [text(c) for c in view.select('.table_header_row .table_col')]
        rows = []
        for row in view.select('.table_row'):
            values = [text(c) for c in row.select('.table_col')]
            if values:
                link = row.get('href') or (row.select_one('a[href]') or {}).get('href') or u
                rows.append({'values': values, 'url': urljoin(u, link)})
        if rows:
            result.append({'headers': headers, 'rows': rows})
    return result

def attempt(label, fn):
    try:
        return fn()
    except Exception as e:
        ERRORS.append(label + ': ' + str(e))
        return None

def refresh_team(team):
    candidate = copy.deepcopy(team)
    ok = []
    s = attempt('team ' + team['id'], lambda: fetch(team['source']))
    if s and 'פרטי קבוצה' in text(s.title):
        tables = views(s, team['source'])
        table_valid = True
        for table in candidate['tables']:
            matches = [v for v in tables if v['headers'] == table['headers'] and len(v['rows']) >= 2]
            if len(matches) == 1:
                table['rows'] = matches[0]['rows']
            else:
                table_valid = False
                ERRORS.append('team ' + team['id'] + ': standings schema mismatch')
        ok.append(table_valid)
    else:
        ok.append(False)
    for field in ['players', 'scorers']:
        old = team.get(field, {})
        if not old.get('source'):
            continue
        def load_field():
            all_views = views(fetch(old['source']), old['source'])
            matches = [v for v in all_views if v['headers'] == old.get('headers')] if field == 'players' else [v for v in all_views if len(v['headers']) == 2 and 'שער' in ' '.join(v['headers'])]
            if len(matches) != 1 or not all(len(r['values']) == len(matches[0]['headers']) for r in matches[0]['rows']):
                raise ValueError('Invalid ' + field + ' table')
            return dict(old, rows=matches[0]['rows'])
        value = attempt(field + ' ' + team['id'], load_field)
        if value:
            candidate[field] = value
        ok.append(value is not None)
    def load_games():
        tables = [v for v in views(fetch(team['games_source']), team['games_source']) if 'תאריך' in v['headers'] and 'משחק' in v['headers']]
        if len(tables) != 1:
            raise ValueError('Missing schedule')
        rows = tables[0]['rows']
        for row in rows:
            if len(row['values']) == 6:
                row['values'].pop(1)
            row['url'] = re.sub(r'&season_id=\d+', '', row['url'])
        if len(rows) < len(team['games']) or not all(len(r['values']) == 5 and re.fullmatch(r'\d{2}/\d{2}/\d{4}', r['values'][0]) and team['name'] in r['values'][1].split(' - ') for r in rows):
            raise ValueError('Incomplete schedule or wrong team')
        return rows
    value = attempt('games ' + team['id'], load_games)
    if value:
        candidate['games'] = value
    ok.append(value is not None)
    if all(ok):
        candidate['fetched_at'] = NOW
    return candidate

def report(g, team):
    v = g['values']; home, away = v[1].split(' - ', 1)
    record = {'date': v[0], 'home': home, 'away': away, 'venue': v[2], 'time': v[3] if v[3] != '00:00' else None, 'source': g['url'], 'completed': False, 'opponent': away if home == team['name'] else home, 'is_home': home == team['name']}
    if 'game_id=-1' in g['url']:
        record['source'] = team['games_source']
        return record
    s = fetch(g['url']); detail = s.select_one('.game-details')
    if not detail:
        raise ValueError('Missing match report')
    h, a = detail.select_one('.team-home a'), detail.select_one('.team-guest a')
    if not h or not a or not (ident(h['href'], 'team_id') == team['id']) != (ident(a['href'], 'team_id') == team['id']):
        raise ValueError('Report belongs to a different team')
    record.update(home=text(h), away=text(a), is_home=ident(h['href'], 'team_id') == team['id'])
    record['opponent'] = record['away'] if record['is_home'] else record['home']
    scores = re.findall(r'\d+', text(detail.select_one('.game-time .total')))
    if v[-1]:
        if len(scores) != 2:
            raise ValueError('Missing final result')
        hs, aws = map(int, scores)
        expected = re.fullmatch(r'(\d+)\s*[-:]\s*(\d+)', v[-1])
        if not expected or [hs, aws] != [int(expected[2]), int(expected[1])]:
            raise ValueError('Report and schedule scores disagree')
        record.update(completed=True, home_score=hs, away_score=aws)
        record['team_score'], record['opponent_score'] = (hs, aws) if record['is_home'] else (aws, hs)
        record['outcome'] = 'W' if record['team_score'] > record['opponent_score'] else 'L' if record['team_score'] < record['opponent_score'] else 'D'
    record['lineups'] = {}
    record['coaches'] = {}
    for side, label in [('HOME', record['home']), ('GUEST', record['away'])]:
        entries = []
        for group in detail.select('[aria-labelledby^="GAME_PLAYER_TYPE_"][aria-labelledby$="_' + side + '"]'):
            group_id = group.get('aria-labelledby', '')
            for link in group.select('a[href*="player_id="]'):
                entries.append({'id': ident(link['href']), 'name': text(link.select_one('.name')), 'number': text(link.select_one('.number')), 'group': group_id, 'source': urljoin(g['url'], link['href'])})
        if entries:
            record['lineups'][side.lower()] = {'name': label, 'players': entries}
        coach = text(detail.select_one('[aria-labelledby="GAME_COACH_' + side + '"] .name'))
        if coach:
            record['coaches'][side.lower()] = coach
    record['goals'] = []
    for event in detail.select('.timeline .node.goal'):
        record['goals'].append({'minute': text(event.select_one('.minute div')), 'name': text(event.select_one('.player')), 'own': ('team1' in event.get('class', [])) == record['is_home']})
    record['events'] = []
    for event in detail.select('.timeline .node'):
        minute, name = text(event.select_one('.minute div')), text(event.select_one('.player'))
        kinds = [c for c in event.get('class', []) if c not in ['node', 'team1', 'team2']]
        if minute and name:
            record['events'].append({'minute': minute, 'name': name, 'kind': ' '.join(kinds), 'own': ('team1' in event.get('class', [])) == record['is_home']})
    # IFA labels converted penalties separately from ordinary goals. Include them
    # only when both teams' event counts exactly reconcile to the final result.
    scoring = [e for e in record['events'] if e['kind'] in ['goal', 'penalty']]
    if record.get('completed') and sum(e['own'] for e in scoring) == record['team_score'] and sum(not e['own'] for e in scoring) == record['opponent_score']:
        record['goals'] = [{k: e[k] for k in ['minute', 'name', 'own']} for e in scoring]
        record['goal_events_reconciled'] = True
    record['fetched_at'] = NOW
    return record

def main():
    data_path, extra_path = BASE / 'data.json', BASE / 'teams/ms-ashdod.json'
    data, extra = json.loads(data_path.read_text()), json.loads(extra_path.read_text())
    old_team = next(t for t in data['teams'] if t['id'] == '1198')
    team = refresh_team(old_team)
    data['teams'][data['teams'].index(old_team)] = team
    existing = {g['source']: g for g in extra['games']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        refreshed = list(pool.map(lambda g: attempt('report ' + g['url'], lambda: report(g, team)), team['games']))
    extra['games'] = [new if new else existing.get(g['url']) for g, new in zip(team['games'], refreshed)]
    extra['games'] = [g for g in extra['games'] if g]
    completed = sorted([g for g in extra['games'] if g.get('completed')], key=lambda g: datetime.strptime(g['date'], '%d/%m/%Y'))
    if completed:
        last = completed[-1]
        side = 'home' if last['is_home'] else 'guest'
        extra['coach'] = last.get('coaches', {}).get(side) or extra.get('coach')
        lineup = last.get('lineups', {}).get(side, {}).get('players', [])
        by_id = {p['id']: p for p in lineup}
        if lineup:
            for p in extra['players']:
                current = by_id.get(p['id'])
                p['captain'] = bool(current and '(C)' in current['name'])
                if current and current['number'].isdigit():
                    p['number'] = int(current['number'])
    extra['goal_minutes'] = [int(re.match(r'\d+', ev['minute'])[0]) for g in extra['games'] if g.get('completed') for ev in g.get('goals', []) if ev['own'] and re.match(r'\d+', ev['minute'])]
    next_games = sorted([g for g in team['games'] if not g['values'][-1] and datetime.strptime(g['values'][0], '%d/%m/%Y').date() >= datetime.now(ZoneInfo('Asia/Jerusalem')).date()], key=lambda g: datetime.strptime(g['values'][0], '%d/%m/%Y'))
    extra.setdefault('opponents', {})
    if next_games:
        names = next_games[0]['values'][1].split(' - ')
        name = next(n for n in names if n != team['name'])
        row = next((r for r in team['tables'][0]['rows'] if r['values'][1] == name), None)
        if row:
            team_id = ident(row['url'], 'team_id')
            source = row['url'] + '&season_id=' + team['season_id']
            def opponent():
                s = fetch(source)
                if 'פרטי קבוצה' not in text(s.title):
                    raise ValueError('Invalid opponent page')
                schedule = 'https://www.football.org.il/team-details/team-games/?' + urlencode({'team_id': team_id, 'season_id': team['season_id']})
                tables = [v for v in views(fetch(schedule), schedule) if 'תאריך' in v['headers'] and 'משחק' in v['headers']]
                if len(tables) != 1:
                    raise ValueError('Missing opponent schedule')
                rows = tables[0]['rows']
                for r in rows:
                    if len(r['values']) == 6:
                        r['values'].pop(1)
                rows = [r for r in rows if len(r['values']) == 5 and name in r['values'][1].split(' - ')]
                if len(rows) < 9:
                    raise ValueError('Invalid opponent rows')
                return {'id': team_id, 'name': name, 'source': source, 'games_source': schedule, 'games': rows, 'fetched_at': NOW}
            result = attempt('opponent ' + name, opponent)
            if result:
                extra['opponents'][team_id] = result
    extra['refresh_errors'] = ERRORS
    extra['refresh_attempted_at'] = NOW
    for path, value in [(data_path, data), (extra_path, extra)]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'team_verified': team['fetched_at'] == NOW, 'reports_verified': sum(bool(g and g.get('fetched_at') == NOW) for g in refreshed), 'opponents': len(extra['opponents']), 'errors': ERRORS}, ensure_ascii=False))
    if not any(g and g.get('fetched_at') == NOW for g in refreshed):
        sys.exit(1)

if __name__ == '__main__':
    main()
