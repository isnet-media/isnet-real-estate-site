"""Monthly comparisons retain their full definition and never rank missing prices."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
definition=json.loads((ROOT/'scripts/super-ashdod/monthly-family-basket.json').read_text())
for city in ('ASHDOD','YAVNE','KGAT','RISHON','HOLON','BATYAM'):
 bundle=json.loads((ROOT/('SUPER.'+city)/'data/city-basket.json').read_text());assert bundle['default_variant']=='monthly'
 m=bundle['variants']['monthly'];assert m['period']=='month' and m['household_size']==[4,5] and m['budget_target_ils']==3500
 assert not m['omitted_products'] and [x['id'] for x in m['products']]==[x['id'] for x in definition]
 assert {x['group'] for x in definition}=={'חלב, ביצים ולחם','מזווה ובישול','עוף, בשר ודגים','פירות וירקות','ניקיון וטואלטיקה'}
 for b in m['branches']:
  found=sum(l['line_total_cents'] is not None for l in b['lines'])
  assert len(b['lines'])==len(definition) and b['complete']==(found==len(definition))
  if b['complete']:
   assert b['total_cents']==sum(g['total_cents'] for g in b['category_totals'].values())
   egg=next(l for l,p in zip(b['lines'],definition) if p.get('target_count'))
   egg_def=next(p for p in definition if p.get('target_count'))
   alt=next((a for a in egg_def.get('alternatives',[]) if a['id']==egg['product_id']),{})
   assert egg['quantity']*alt.get('package_count',egg_def['package_count'])==120
  else:
   assert b['total_cents'] is None and b['id'] not in m['winner_ids']+m['most_expensive_ids']
 if m['ranking_available']:
  totals=[b['total_cents'] for b in m['branches'] if b['complete']]
  assert m['gap_cents']==max(totals)-min(totals) and m['annual_gap_cents']==m['gap_cents']*12
  assert m['average_cents']==round(sum(totals)/len(totals))
 else:assert m['annual_gap_cents'] is None
 print(city,'verified: fixed monthly quantities, complete-only ranking, category sums, equal egg count and annual arithmetic')
