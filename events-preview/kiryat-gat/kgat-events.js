/* City-owned published snapshot; no dependency on another city's CMS edition. */
(()=>{
const snapshot=window.ISNET_CITY_BOOTSTRAP;
const request=(name)=>fetch('data/'+name+'.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Event feed unavailable');return r.json()});
const data=()=>snapshot?Promise.resolve(snapshot):request('events');
window.ISNET_PUBLIC_CMS={loadSource:data,loadCards:data,loadHub:data,publishedEvents:()=>Promise.resolve([]),metrics:{}};
const sportEligible=e=>{
 if(e.is_home_game===true&&e.representative_team===true&&e.home_team)return true;
 const title=e.title||'';
 if(/הרצא|אימון (?:מוח|זיכרון)|כושר (?:מוח|קוגניטיבי)/.test(title))return false;
 if(/מרוץ|מירוץ|מרתון|טריאתלון/.test(title))return true;
 if(/טורניר|אליפות|תחרו[תי]/.test(title)&&/ספורט|כדור|שחייה|שחיה|ריצה|אתלטיקה|אופניים|טניס|פאדל|ג[׳']ודו|קראטה|התעמלות|שחמט|אגרוף|בדמינטון/.test(title))return true;
 return !/גיל\s*השלישי|גילאי\s*60|60\+|גמלאים|גימלאים/.test(title)&&/אימון פתוח|יום ספורט|צעדה|הליכה עממית|רכיבה (?:עממית|קהילתית)|ספורט עממי/.test(title);
};
window.KGAT_EVENTS={sportEligible,matches:(e,ids)=>(ids.has(e.category)&&(e.category!=='sport'||sportEligible(e)))||(e.category_memberships||[]).some(x=>ids.has(x.category)&&(x.category!=='sport'||sportEligible(e)))||(ids.has('seniors')&&(e.audiences||[]).includes('seniors'))||(ids.has('kids')&&(e.audiences||[]).includes('kids'))};
window.KGAT_EVENTS.renderOffers=e=>{
 document.getElementById('kgat-friends-offer')?.remove();
 const offer=e.friends_offer;if(!offer)return;
 let url;try{url=new URL(offer.url)}catch{return}
 if(url.protocol!=='https:'||!['friends-hist.co.il','www.friends-hist.co.il'].includes(url.hostname))return;
 const anchor=document.getElementById('heroBuy')?.parentElement;if(!anchor)return;
 const box=document.createElement('section');box.id='kgat-friends-offer';box.setAttribute('aria-label','אפשרות הזמנה ב־FRIENDS');box.style.cssText='padding:16px;margin-top:16px;border:1px solid #bfa57088;border-radius:12px;background:#1b2228;color:#f5f1e7;line-height:1.7';
 const title=document.createElement('strong');title.textContent='אפשרות הזמנה ב־FRIENDS';box.append(title);
 const facts=document.createElement('p');facts.style.margin='8px 0';facts.textContent=[offer.regular_price_ils!=null?'מחיר רגיל ב־FRIENDS: '+offer.regular_price_ils+' ₪':null,offer.member_price_ils!=null?'מחיר לחברי הסתדרות זכאים: '+offer.member_price_ils+' ₪':null].filter(Boolean).join(' · ');box.append(facts);
 const note=document.createElement('p');note.style.cssText='font-size:14px;margin:8px 0';note.textContent='מחיר החבר מותנה בזכאות ובתנאי ההטבה. יש לבדוק זמינות ומחיר סופי בתהליך ההזמנה.';box.append(note);
 const link=document.createElement('a');link.href=url.href;link.target='_blank';link.rel='noopener noreferrer';link.textContent='לפרטים ולהזמנה ב־FRIENDS ↗';link.style.cssText='color:#f3dfb4;text-decoration:underline';box.append(link);anchor.after(box);
};
})();
