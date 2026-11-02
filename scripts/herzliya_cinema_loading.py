"""Keep Herzliya cinema rendering independent of the full event board and detail payload."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'events-preview/herzliya/data'

def build_listing():
 data=json.loads((D/'cinema.json').read_text());keys={'id','title','synopsis','genres','runtime_minutes','age_rating','poster_url','poster_credit','trailer_youtube_id','trailer_page_url','is_family','family_catalog_source_url','aliases'}
 cache=json.loads((D/'cinema-poster-cache.json').read_text()) if (D/'cinema-poster-cache.json').exists() else {}
 movies=[]
 for movie in data['movies']:
  row={k:v for k,v in movie.items() if k in keys}
  text=row.get('synopsis','');row['synopsis']=text[:280].rsplit(' ',1)[0]+'…' if len(text)>280 else text
  if movie.get('poster_verification'):row['poster_verification']={'url':movie['poster_verification'].get('url')}
  if movie.get('poster_url') in cache:
   row['poster_url']=cache[movie['poster_url']]['path'];row['poster_verification']={'url':row['poster_url']}
   row['poster_credit']=row.get('poster_credit') or 'כרזה: סינמה סיטי — מקור רשמי'
  row['venues']=[{k:v for k,v in venue.items() if k in {'id','name','schedule','article_url'}} for venue in movie['venues']]
  movies.append(row)
 listing={'updated_at':data['updated_at'],'movies':movies}
 (D/'cinema-listing.json').write_text(json.dumps(listing,ensure_ascii=False,separators=(',',':'))+'\n')
 return listing

def optimize(content,name,suffix):
 if suffix=='.html' and name=='index.html':
  # Shared inline feed avoids another network round trip before the first film cards.
  listing=json.loads((D/'cinema-listing.json').read_text())
  packed=json.dumps(listing,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
  content=content.replace('<head>','<head><meta charset="utf-8"><script>window.ISNET_CINEMA_BOOTSTRAP='+packed+';</script>',1)
  content=content.replace('href="cinema.html"','href="#cinema"')
  content=re.sub(r'<body([^>]*)>',r'<body\1><script>if(location.hash==="#cinema")document.body.classList.add("cinemaMode");</script>',content,count=1)
 if suffix=='.js' and Path(name).name=='app.js':
  content=content.replace('function cinemaToday(){return new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Jerusalem",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date())}', '''const cinemaDayFormatter=new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Jerusalem",year:"numeric",month:"2-digit",day:"2-digit"});
const cinemaShortDateFormatter=new Intl.DateTimeFormat("he-IL",{weekday:"short",day:"numeric",month:"short"});
let cinemaDayValue="",cinemaDayCheckedAt=0,cinemaRenderSignature="";
function cinemaToday(){const now=Date.now();if(!cinemaDayValue||now-cinemaDayCheckedAt>=1000){cinemaDayValue=cinemaDayFormatter.format(new Date(now));cinemaDayCheckedAt=now;}return cinemaDayValue;}''')
  content=content.replace('function today(){return localDate(new Intl.DateTimeFormat("sv-SE",{timeZone:"Asia/Jerusalem",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date()))}', 'function today(){return localDate(cinemaToday())}')
  # Reuse the short-date formatter for each card; never allocate one per screening.
  content=content.replace('new Intl.DateTimeFormat("he-IL",{weekday:"short",day:"numeric",month:"short"}).format(d)','cinemaShortDateFormatter.format(d)')
  content=content.replace('function render(){','function render(){\n  if(state.cinemaOpen)return;')
  content=content.replace('render();state.cinemaOpen=location.hash==="#cinema";renderCinema();','state.cinemaOpen=location.hash==="#cinema";render();renderCinema();')
  content=content.replace('    renderCategories();\n    history.replaceState(null,"",location.pathname+location.search);','    render();\n    history.replaceState(null,"",location.pathname+location.search);')
  content=content.replace('fetch("data/cinema.json",{cache:"no-cache"})','(window.ISNET_CINEMA_BOOTSTRAP?Promise.resolve({ok:true,json:()=>Promise.resolve(window.ISNET_CINEMA_BOOTSTRAP)}):fetch("data/cinema-listing.json",{cache:"no-cache"}))')
  content=content.replace('state.cinema=window.CinemaEditorial.unique(cinema.movies||[]);','state.cinema=window.CinemaEditorial.unique(cinema.movies||[]);state.cinemaEditorialReady=true;')
  content=content.replace('if(!state.cinemaOpen){grid.innerHTML="";return}', 'if(!state.cinemaOpen){grid.innerHTML="";cinemaRenderSignature="";return}\n  const signature=[state.cinemaUpdatedAt,state.cinema.length,state.cinemaVenue,state.cinemaAudience,state.cinemaQuery,state.cinemaLimit||24,state.cinemaEditorialReady,cinemaToday()].join("|");\n  if(signature===cinemaRenderSignature)return;cinemaRenderSignature=signature;')
  content=content.replace('grid.innerHTML=arr.length?arr.map(cinemaCard).join(""):', 'grid.innerHTML=arr.length?arr.slice(0,state.cinemaLimit||24).map(cinemaCard).join("")+(arr.length>(state.cinemaLimit||24)?\'<button id="cinemaLoadMore" type="button" class="cinemaBackButton" style="grid-column:1/-1;justify-self:center">עוד סרטים ↓</button>\':\'\'):')
  content=content.replace('  if($("cinemaResetFilters"))', '  if($("cinemaLoadMore"))$("cinemaLoadMore").onclick=()=>{state.cinemaLimit=(state.cinemaLimit||24)+24;renderCinema()};\n  if($("cinemaResetFilters"))',1)
  content=content.replace('state.cinemaVenue=b.dataset.cinema;', 'state.cinemaLimit=24;state.cinemaVenue=b.dataset.cinema;').replace('state.cinemaAudience=b.dataset.audience;', 'state.cinemaLimit=24;state.cinemaAudience=b.dataset.audience;').replace('state.cinemaQuery=e.target.value;', 'state.cinemaLimit=24;state.cinemaQuery=e.target.value;')
  content=content.replace('if(/^https:\\/\\//.test(movie.poster_url||"")','if(/^(?:https:\\/\\/|\\/)/.test(movie.poster_url||"")')
  content=content.replace('href="cinema.html"','href="./#cinema"')
  content=content.replace('https://hotcinema.co.il/theater/5','https://www.cinema-city.co.il/city/glilot').replace('סינמטק הרצליה הרצליה ←','סינמה סיטי גלילות ←')
  # Cheap timing marks support read-only browser verification of first usable cards.
  content=content.replace('function renderCinema(){','function renderCinema(){\n  const cinemaRenderStart=performance.now();')
  content=content.replace('  cinemaSpotlight(arr);','  cinemaSpotlight(arr);')
  marker='  const updated=$("cinemaUpdated");'
  content=content.replace(marker,'  section.dataset.cinemaRenderMs=(performance.now()-cinemaRenderStart).toFixed(1);section.dataset.cinemaReadyMs||=performance.now().toFixed(1);performance.measure("herzliya-cinema-render",{start:cinemaRenderStart,end:performance.now()});\n  if(!performance.getEntriesByName("herzliya-cinema-ready").length)performance.mark("herzliya-cinema-ready");\n'+marker)
 if suffix=='.js' and name=='movie.js':
  content=content.replace('    await window.CinemaEditorial?.ready;','    // Film facts and sessions render before optional shared editorial/index requests finish.')
  content=content.replace('    window.CinemaEditorial?.mount(movie);','    window.CinemaEditorial?.mount(movie);\n    window.CinemaEditorial?.ready.then(()=>window.CinemaEditorial.mount(movie));')
 return content
