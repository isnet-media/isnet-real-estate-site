from audit_purchase_links import check
class Response:
    encoding='utf-8'
    def __init__(self,code,text='',headers=None):self.status_code=code;self.text=text;self.headers=headers or {}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,chunk_size):yield self.text.encode()
class Session:
    def __init__(self,*responses):self.responses=list(responses);self.urls=[]
    def get(self,url,**kwargs):self.urls.append(url);return self.responses.pop(0)
def run(code,text='',url='https://example.com/event/1'):
    return check(url,session=Session(Response(code,text)),guard=lambda u:True)
assert run(404)['state']=='broken'
assert run(410)['state']=='broken'
assert run(403)['state']=='unverified'
assert run(429)['state']=='unverified'
assert run(503)['state']=='unverified'
assert run(200,'Just a moment')['state']=='unverified'
assert run(200,'event information')['state']=='reachable'
assert run(200,'home',url='https://example.com/')['state']=='needs_review'
session=Session(Response(302,headers={'Location':'http://127.0.0.1/private'}))
assert check('https://example.com/event',session=session,guard=lambda u:'127.0.0.1' not in u)['state']=='unverified'
assert len(session.urls)==1
assert check('#updates',session=Session(),guard=lambda u:False)['state']=='unverified'
print('PASS: broken vs blocked, 5xx uncertainty, human checks, homepages, redirect destination safety, invalid URLs')
