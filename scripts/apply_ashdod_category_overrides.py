"""Apply reviewed Ashdod event classifications only; no network or publication."""
import html,json
from pathlib import Path
def apply_ashdod_category_overrides(events,root):
 path=Path(root)/'events-preview/ashdod/data/category-overrides.json'
 if not path.is_file():return 0
 catalog=json.loads(path.read_text())
 rules={html.unescape(r['title']).strip():r for r in catalog['rules']}
 count=0
 for event in events:
  if event.get('category')=='tour':
   event.update(category='seniors',subcategory='senior-trips');count+=1
  else:
   rule=rules.get(html.unescape(str(event.get('title') or '')).strip())
   if rule and (rule.get('all_categories') is True or event.get('category')=='community'):
    event.update(category=rule['category'],subcategory=rule['subcategory']);count+=1
 return count
