"""Keep verified Yavne promotional images and mobile thumbnails on our own host."""
import json
import cache_event_images_allowlisted as cache
import generate_event_thumbnails as thumbs
ROOT=cache.ROOT/'events-preview/yavne'
def main():
 cache.DATA=ROOT/'data/events.json';cache.OUT=ROOT/'assets/events'
 cache.ALLOWED={'www.htyavne.co.il','htyavne.co.il','yavne-matnasim.smarticket.co.il','static.smarticket.co.il'}
 cache.main()
 thumbs.EVENT_ROOT=ROOT;thumbs.DATA=cache.DATA;thumbs.OUT=ROOT/'assets/event-thumbs';thumbs.main()
 movies=json.loads((ROOT/'data/cinema.json').read_text());events=json.loads(cache.DATA.read_text())['events']
 for movie in movies['movies']:
  event=next((e for e in events if e['title']==movie['title'] and e.get('image_publishable')),None)
  if event:movie['poster_url']=event['image_url']
 (ROOT/'data/cinema.json').write_text(json.dumps(movies,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
