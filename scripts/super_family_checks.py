"""Publication guard for fixed family products and honest partial comparisons."""
def verify_fixed_family(basket,definition,branch_ids):
 assert [(p['id'],p['quantity']) for p in basket['products']]==[(p['id'],p['quantity']) for p in definition]
 assert not basket.get('omitted_products')
 branches=basket['branches'];assert len(branches)==len(branch_ids) and {b['id'] for b in branches}==set(branch_ids)
 complete=[]
 for b in branches:
  assert [l['id'] for l in b['lines']]==[p['id'] for p in definition]
  found=sum(l['line_total_cents'] is not None for l in b['lines'])
  assert b['found']==found and b['complete']==(found==len(definition))
  if b['complete']:
   assert b['total_cents']==sum(l['line_total_cents'] for l in b['lines']);complete.append(b)
  else:
   assert b['total_cents'] is None and b['id'] not in basket['winner_ids']+basket['most_expensive_ids']
 assert basket['complete_branch_count']==len(complete) and basket['ranking_available']==(len(complete)>=2)
 assert basket['average_cents']==(round(sum(b['total_cents'] for b in complete)/len(complete)) if complete else None)
 if len(complete)>=2:
  low=min(b['total_cents'] for b in complete);high=max(b['total_cents'] for b in complete)
  assert basket['minimum_cents']==low and basket['maximum_cents']==high and basket['gap_cents']==high-low
  assert basket['gap_percent_of_cheapest']==round((high-low)/low*100,2)
  assert set(basket['winner_ids'])=={b['id'] for b in complete if b['total_cents']==low}
  assert set(basket['most_expensive_ids'])=={b['id'] for b in complete if b['total_cents']==high}
 else:
  assert basket['minimum_cents'] is None and basket['maximum_cents'] is None and basket['gap_cents'] is None
  assert not basket['winner_ids'] and not basket['most_expensive_ids']
