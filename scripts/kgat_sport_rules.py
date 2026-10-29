"""Sport listings are fixtures, competitions or public participation events."""
import re
SENIOR=re.compile(r'גיל\s*השלישי|גילאי\s*60|60\+|גמלאים|גימלאים')
def sport_kind(title,text=''):
 if re.search(r'הרצא|אימון (?:מוח|זיכרון)|כושר (?:מוח|קוגניטיבי)',title):return None
 if re.search(r'מרוץ|מירוץ|מרתון|טריאתלון',title):return 'competition'
 if re.search(r'טורניר|אליפות|תחרו[תי]',title) and re.search(r'ספורט|כדור|שחייה|שחיה|ריצה|אתלטיקה|אופניים|טניס|פאדל|ג[׳\u0027]ודו|קראטה|התעמלות|שחמט|אגרוף|בדמינטון',title):return 'competition'
 if SENIOR.search(title):return None
 if re.search(r'אימון פתוח|יום ספורט|צעדה|הליכה עממית|רכיבה (?:עממית|קהילתית)|ספורט עממי',title):return 'public_activity'
 return None
def eligible(e):
 if e.get('is_home_game') is True and e.get('representative_team') is True and e.get('home_team'):return True
 return sport_kind(e.get('title','')) is not None
def repair(e):
 if e.get('category')!='sport':return e
 if eligible(e):
  e['sport_event_kind']='home_game' if e.get('is_home_game') else sport_kind(e['title'])
  return e
 senior=bool(SENIOR.search(e.get('title',''))) or e.get('activity_type')=='seniors'
 e['category']='seniors' if senior else 'community'
 e['subcategory']='senior-health' if senior else 'community-events'
 e['category_memberships']=[m for m in e.get('category_memberships',[]) if m.get('category')!='sport']
 membership={'category':e['category'],'subcategory':e['subcategory']}
 if membership not in e['category_memberships']:e['category_memberships'].append(membership)
 if senior:e['audiences']=sorted(set(e.get('audiences',[]))|{'seniors'})
 e.pop('sport_event_kind',None)
 return e
