const form = document.querySelector('#match-form');
const status = document.querySelector('.match-status');
let result = document.querySelector('#match-result');
const landing = new URL('/astrology/compatibility/',location.origin);
let pending;
const canonical = document.querySelector('link[rel="canonical"]');
const titleSuffix = ' | עולם האסטרולוגיה שלך';
function setPageIdentity(url,title) {
  document.title = title;
  if (canonical) canonical.href = new URL(url.pathname,'https://isnet.co.il');
}


function showStatus(message = '') {
  status.textContent = message;
  status.hidden = !message;
}
function stopRequest() {
  pending?.abort();
  pending = undefined;
}
function focusAndScroll(target) {
  target.focus({preventScroll:true});
  target.scrollIntoView({block:'start',behavior:'instant'});
}
function urlForSelection() {
  return new URL([form.elements.first.value,form.elements.second.value].sort().join('-')+'/',landing);
}
function preselect() {
  const sign = new URLSearchParams(location.search).get('sign');
  if (sign && [...form.elements.first.options].some(option=>option.value===sign)) {
    form.elements.first.value = sign;
  }
}
function reset(shouldFocus, push) {
  stopRequest();
  showStatus();
  result.hidden = true;
  form.reset();
  form.elements.first.value = '';
  form.elements.second.value = '';
  if (push) history.pushState(null,'',landing);
  preselect();
  setPageIdentity(landing,'התאמה זוגית לפי מזלות'+titleSuffix);
  if (shouldFocus) focusAndScroll(form.elements.first);
}
async function loadPair(url,push,shouldFocus) {
  stopRequest();
  const controller = new AbortController();
  pending = controller;
  showStatus('טוען את הקריאה הזוגית…');
  try {
    const response = await fetch(url,{signal:controller.signal});
    if (!response.ok) throw new Error('pair unavailable');
    const documentForPair = new DOMParser().parseFromString(await response.text(),'text/html');
    const pair = documentForPair.querySelector('.match-result');
    if (!pair) throw new Error('pair unavailable');
    if (pending !== controller) return;
    if (!push) {
      const fromPair = documentForPair.querySelector('#match-form');
      form.elements.first.value = fromPair.elements.first.value;
      form.elements.second.value = fromPair.elements.second.value;
    }
    result.replaceWith(pair);
    result = pair;
    if (push) history.pushState(null,'',url);
    setPageIdentity(url,documentForPair.title);
    showStatus();
    if (shouldFocus) focusAndScroll(result.querySelector('h2'));
  } catch (cause) {
    if (cause.name !== 'AbortError') showStatus('לא הצלחנו לטעון את הקריאה. אפשר לנסות שוב.');
  } finally {
    if (pending === controller) pending = undefined;
  }
}
preselect();
form.addEventListener('submit',event=>{
  event.preventDefault();
  if (form.reportValidity()) loadPair(urlForSelection(),true,true);
});
document.addEventListener('click',event=>{
  if (event.target.closest('.match-reset')) {
    event.preventDefault();
    reset(true,true);
  }
});
window.addEventListener('popstate',()=>{
  const url = new URL(location.href);
  if (url.pathname===landing.pathname) reset(false,false);
  else loadPair(url,false,false);
});
