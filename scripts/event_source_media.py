"""Read only the current event's media; lazy placeholders and nearby-event cards are never donors."""
import re
from urllib.parse import urljoin,urlsplit
BAD=re.compile(r'^(?:data:|blob:)|placeholder|favicon|logo|no_pic|eventNew\.jpg|artistShadow|spacer\.|blank\.',re.I)
def valid_image(url):return bool(url and urlsplit(url).scheme in ('http','https') and not BAD.search(url))
def lazy_image(img,base):
 if img is None:return None
 for key in ('data-lazy-src','data-src','src'):
  value=urljoin(base,img.get(key,'')) if img.get(key) else None
  if valid_image(value):return value
 return None
def friends_image(soup,url,listing=None):
 # The main image is distinct from the recommendation strip, site logos and icons.
 main=lazy_image(soup.select_one('.wrap_main_img img'),url)
 if main:return main
 return listing if valid_image(listing) else None
