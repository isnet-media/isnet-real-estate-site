"""One transport retry budget, without contacting any retailer."""
from unittest.mock import Mock,patch
import requests
from urllib3.exceptions import ConnectTimeoutError,ReadTimeoutError,MaxRetryError
from urllib3.response import HTTPResponse
import refresh_super_prices as c

retry=c.session().get_adapter('https://official.example/').max_retries
for error in (ConnectTimeoutError('blocked'),ReadTimeoutError(None,'/','slow')):
 try:retry.increment(method='GET',url='https://official.example/',error=error)
 except MaxRetryError:pass
 else:raise AssertionError('Adapter multiplied the outer transport retry budget')
# HTTP status handling remains bounded and enabled for GET/HEAD only.
assert retry.is_retry('GET',503) and retry.is_retry('HEAD',429)
assert not retry.is_retry('POST',503) and not retry.is_retry('GET',403)
remaining=retry
for _ in range(2):remaining=remaining.increment(method='GET',url='/',response=HTTPResponse(status=503))
try:remaining.increment(method='GET',url='/',response=HTTPResponse(status=503))
except MaxRetryError:pass
else:raise AssertionError('HTTP retry limit exceeded')
for method in ('GET','POST'):
 for failure in (requests.ConnectionError,requests.Timeout):
  s=Mock();s.request.side_effect=failure('blocked')
  with patch.object(c.time,'sleep'),patch.object(c.random,'uniform',return_value=0):
   try:c.request(s,'https://official.example/',method=method)
   except failure:pass
   else:raise AssertionError('Transport failure swallowed')
  assert s.request.call_count==3,(method,failure,s.request.call_count)
  assert all(call.kwargs['timeout']==(30,50) for call in s.request.call_args_list)
 s=Mock();s.request.return_value.raise_for_status.side_effect=requests.HTTPError('403')
 try:c.request(s,'https://official.example/',method=method)
 except requests.HTTPError:pass
 else:raise AssertionError('HTTP refusal swallowed')
 assert s.request.call_count==1,'Access refusal retried'
print('Passed: exactly three transport attempts for GET/POST, no nested connect/read retries, bounded HTTP retries and no 403 retry')
