import { localDayPositions, localInstants, positions, signIndex } from './rising-positions.mjs';
import { glyphs, readings, roles, roleSummaries, signNames, synthesis } from './rising-readings.mjs';

const canonical = 'https://isnet.co.il/astrology/rising/';
const form = document.querySelector('#rising-form');
const fields = form.elements;
const result = document.querySelector('#rising-result');
const error = document.querySelector('#rising-error');
const citySuggestions = document.querySelector('#rising-city-suggestions');
const countrySuggestions = document.querySelector('#rising-country-suggestions');
let revision = 0;

function node(tag, content, className) {
  const element = document.createElement(tag);
  if (content) element.textContent = content;
  if (className) element.className = className;
  return element;
}

const normalize = value => value.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f\u0591-\u05bd\u05bf-\u05c7]/g,'').replace(/[-‐־’']/g,' ').replace(/\s+/g,' ').trim();
const translations = {
  'new york':'ניו יורק', london:'לונדון', paris:'פריז', berlin:'ברלין', moscow:'מוסקבה',
  rome:'רומא', madrid:'מדריד', barcelona:'ברצלונה', athens:'אתונה', istanbul:'איסטנבול',
  toronto:'טורונטו', montreal:'מונטריאול', 'los angeles':'לוס אנגלס', miami:'מיאמי',
  chicago:'שיקגו', tokyo:'טוקיו', sydney:'סידני', melbourne:'מלבורן', dubai:'דובאי',
  singapore:'סינגפור', amsterdam:'אמסטרדם', prague:'פראג', vienna:'וינה', warsaw:'ורשה',
  'buenos aires':'בואנוס איירס', 'sao paulo':'סאו פאולו', kyiv:'קייב', kiev:'קייב',
  bangkok:'בנגקוק', brussels:'בריסל', bucharest:'בוקרשט', budapest:'בודפשט', cairo:'קהיר',
  lisbon:'ליסבון', stockholm:'סטוקהולם', copenhagen:'קופנהגן', oslo:'אוסלו', reykjavik:'רייקיאוויק'
};
const countryAliases = {
  'ישראל':'israel','צרפת':'france','בריטניה':'united kingdom','אנגליה':'united kingdom',
  'ארצות הברית':'united states','ארה"ב':'united states','ארה״ב':'united states','usa':'united states',
  'united states of america':'united states','גרמניה':'germany','איטליה':'italy','ספרד':'spain',
  'הולנד':'netherlands','יוון':'greece','טורקיה':'turkey','קנדה':'canada','אוסטרליה':'australia',
  'רוסיה':'russia','אוקראינה':'ukraine','פולין':'poland','הודו':'india','מרוקו':'morocco','יפן':'japan',
  'שוויץ':'switzerland','אוסטריה':'austria','ברזיל':'brazil','ארגנטינה':'argentina','מצרים':'egypt',
  'פורטוגל':'portugal','בלגיה':'belgium','רומניה':'romania','הונגריה':'hungary','שוודיה':'sweden',
  'דנמרק':'denmark','נורווגיה':'norway','איסלנד':'iceland','דרום אפריקה':'south africa','ניו זילנד':'new zealand'
};
const countryKey = text => countryAliases[normalize(text)] || normalize(text);
const cityAliases = {'new york city':'new york','תל אביב יפו':'תל אביב','תל אביב-יפו':'תל אביב','גבעתיים':'givatayim'};
const cityKey = text => cityAliases[normalize(text)] || normalize(text);
const countryName = row => row[1].split(',').at(-1).trim();
const province = row => row[1].split(',').slice(0,-1).join(',').trim();
const cityLabel = row => translations[normalize(row[5])] || translations[normalize(row[0])] || row[0];
const fullLabel = row => [cityLabel(row),province(row)].filter(Boolean).join(', ');

let cityLoad;
function loadCities() {
  if (!cityLoad) cityLoad = fetch(new URL('./rising-cities.json',import.meta.url))
    .then(response => {
      if (!response.ok) throw new Error('city data unavailable');
      return response.json();
    })
    .then(rows => rows.map(row => ({
      row, nation: countryKey(countryName(row)),
      names: [...new Set([cityKey(row[0]),cityKey(row[5]),cityKey(cityLabel(row)),cityKey(fullLabel(row)),cityKey([row[0],province(row)].filter(Boolean).join(' ')),cityKey([row[0],province(row)].filter(Boolean).join(', '))].filter(Boolean))]
    })))
    .catch(error => { cityLoad = undefined; throw error; });
  return cityLoad;
}

function showError(message = '', field) {
  error.textContent = message;
  error.hidden = !message;
  if (field) field.focus();
}

function suggest(list,values) {
  list.replaceChildren(...[...new Set(values)].slice(0,12).map(value => {
    const item = node('option');
    item.value = value;
    return item;
  }));
}

form.addEventListener('input',async event => {
  const current = ++revision;
  showError();
  result.hidden = true;
  if (![fields.city,fields.country].includes(event.target)) return;
  try {
    const cities = await loadCities();
    if (revision !== current) return;
    const city = cityKey(fields.city.value);
    const nation = countryKey(fields.country.value);
    const matches = cities.filter(item => !city || item.names.some(name => name.startsWith(city)));
    suggest(citySuggestions,matches.filter(item => !nation || item.nation.startsWith(nation))
      .flatMap(({row}) => [cityLabel(row),fullLabel(row)]));
    suggest(countrySuggestions,matches.filter(item => !nation || item.nation.startsWith(nation))
      .map(({row}) => countryName(row)));
  } catch {
    // A later edit or submission retries the local gazetteer.
  }
});

function synchronize() {
  fields.hour.disabled = fields.unknown.checked;
}
form.addEventListener('change',synchronize);
synchronize();
fields.hour.addEventListener('input', () => {
  const digits = fields.hour.value.replace(/\D/g,'').slice(0,4);
  fields.hour.value = digits.length > 2 ? digits.slice(0,2)+':'+digits.slice(2) : digits;
});

function matchedLocation(cities,city,nation) {
  const exact = cities.filter(item => item.nation===nation && item.names.includes(city));
  if (!exact.length) return null;
  const first = exact[0].row;
  if (exact.some(({row}) => row[4] !== first[4] || Math.hypot(row[2]-first[2],row[3]-first[3])>.1)) return false;
  return [first[2],first[3],first[4]];
}

const titles = ['שמש','ירח','אופק'];

function card(index, candidates, degrees, unavailable) {
  const card = node('article',null,'rising-card rising-card--'+index);
  const known = candidates.length === 1;
  card.append(node('span',known ? glyphs[candidates[0]]+'\uFE0E' : '—','rising-glyph'));
  card.append(node('h3',roles[index]));
  card.append(node('p',known ? signNames[candidates[0]] : candidates.length > 1 ? candidates.map(sign => signNames[sign]).join(' או ') : 'לא ניתן לקבוע','rising-card-name'));
  if (known && degrees?.[index] != null) {
    const within = degrees[index] % 30;
    card.append(node('p',`${Math.floor(within*100)/100}° במזל`,'rising-degree'));
    if (within < 0.15 || within > 29.85) card.append(node('small','קרוב לגבול בין מזלות. כדאי לבדוק מחדש את דיוק שעת הלידה והמיקום.'));
  }
  if (known) card.append(node('p',roleSummaries[index]));
  else card.append(node('p',unavailable[index]));
  return card;
}

function reading(index, sign) {
  const [title, interpretation, practice] = readings[index][sign];
  const details = node('details',null,'rising-reading');
  const heading = node('summary',`${titles[index]} ב${signNames[sign]} · ${title}`);
  details.append(heading,node('p',interpretation),node('h4','משהו שאפשר לנסות'),node('p',practice));
  return details;
}

function render(sets,degrees,unavailable) {
  const known = sets.map(signs => signs.length === 1 ? signs[0] : null);
  result.replaceChildren();
  const heading = node('h2','שלושת המזלות שלי');
  heading.id = 'rising-result-heading';
  heading.tabIndex = -1;
  result.append(heading);
  const cards = node('div',null,'rising-cards');
  sets.forEach((signs,index) => cards.append(card(index,signs,degrees,unavailable)));
  result.append(cards);
  if (known.every(sign => sign !== null)) {
    const combined = node('section',null,'rising-synthesis');
    combined.append(node('h3','איך שלושת המזלות שלכם מתחברים?'));
    for (const [theme,message] of synthesis(...known)) {
      const block = node('article');
      block.append(node('h4',theme),node('p',message));
      combined.append(block);
    }
    result.append(combined);
  } else result.append(node('p','קריאה משולבת מלאה זמינה כשאפשר לזהות בוודאות את שלושת המזלות.','rising-result-note'));
  if (known.some(sign => sign !== null)) {
    const readingsArea = node('section',null,'rising-reading-list');
    readingsArea.append(node('h3','להעמיק בכל אחד מהמזלות'));
    known.forEach((sign,index) => { if (sign !== null) readingsArea.append(reading(index,sign)); });
    result.append(readingsArea);
  }
  result.append(sharing(known));
  result.hidden = false;
  heading.focus();
}

function parseBirthDate(dayText, monthText, yearText) {
  const values = [dayText, monthText, yearText].map(value => value.trim());
  if (!/^\d{1,2}$/.test(values[0]) || !/^\d{1,2}$/.test(values[1]) || !/^\d{4}$/.test(values[2])) return null;
  const [day, month, year] = values.map(Number);
  if (year < 1900 || year > 2099) return null;
  const date = new Date(Date.UTC(year, month - 1, day));
  if (date.getUTCDate() !== day || date.getUTCMonth() + 1 !== month) return null;
  return [year, String(month).padStart(2, '0'), String(day).padStart(2, '0')].join('-');
}

form.addEventListener('submit',async event => {
  event.preventDefault();
  showError();
  result.hidden = true;
  const birthDate = parseBirthDate(fields.day.value, fields.month.value, fields.year.value);
  if (!birthDate) {
    showError('הקלידו תאריך לידה תקין: יום, חודש ושנה בת ארבע ספרות בין 1900 ל־2099.',fields.day);
    return;
  }
  if (!fields.unknown.checked && !/^([01]\d|2[0-3]):[0-5]\d$/.test(fields.hour.value)) {
    showError('כתבו שעת לידה בפורמט 24 שעות (למשל 14:35), או סמנו ששעת הלידה לא ידועה.',fields.hour);
    return;
  }
  const city = cityKey(fields.city.value);
  const nation = countryKey(fields.country.value);
  if (!city || !nation) {
    showError('הקלידו את עיר הלידה ואת מדינת הלידה.',city ? fields.country : fields.city);
    return;
  }
  const current = ++revision;
  let cities;
  try { cities = await loadCities(); }
  catch {
    if (current === revision) showError('רשימת הערים לא זמינה כרגע. אפשר ללחוץ שוב על כפתור החישוב.');
    return;
  }
  if (current !== revision) return;
  const place = matchedLocation(cities,city,nation);
  if (!place) {
    showError(place===false ? 'יש כמה ערים בשם הזה באותה מדינה. בחרו הצעה שמציינת גם מחוז, או הקלידו עיר ומחוז.' :
      'לא מצאנו עיר תואמת במדינה שהוזנה. בדקו את האיות או נסו את שם העיר באנגלית.',fields.city);
    return;
  }
  const [lat,lon,zone] = place;
  try {
    if (fields.unknown.checked) {
      const sets = localDayPositions(birthDate,zone);
      if (!sets) {
        showError('תאריך הלידה אינו קיים בלוח המקומי של אזור הזמן שנבחר. בדקו את התאריך והמקום.');
        return;
      }
      render(sets,null,['השמש החליפה מזל באותו יום. דרושה שעה.','הירח החליף מזל באותו יום. דרושה שעה.','חישוב האופק דורש שעת לידה.']);
      return;
    }
    const instants = localInstants(birthDate,fields.hour.value,zone);
    if (!instants.length) {
      showError('השעה לא התקיימה בתאריך ובאזור הזמן שנבחרו. ייתכן שמדובר במעבר לשעון קיץ.',fields.hour);
      return;
    }
    const calculated = instants.map(instant => positions(instant,lat,lon));
    const sets = titles.map((_title,index) => [...new Set(calculated.map(row => signIndex(row[index])).filter(sign => sign !== null))]);
    if (instants.length > 1) sets[2] = [];
    const crossover = 'השעה המקומית התקיימה פעמיים בגלל שינוי שעון. שעה עם ציון ההיסט מ־UTC דרושה להכרעה.';
    render(sets,instants.length === 1 ? calculated[0] : null,[crossover,crossover,instants.length > 1 ? crossover : 'חיתוך האופק אינו חד־משמעי בנקודה הזאת.']);
  } catch {
    showError('לא ניתן לחשב לפי הפרטים שהוזנו. בדקו שוב את תאריך הלידה ואת פרטי המקום.');
  }
});

function shareImage(known) {
  const canvas = document.createElement('canvas');
  canvas.width = 1200;
  canvas.height = 1200;
  const ctx = canvas.getContext('2d');
  const sky = ctx.createLinearGradient(100,0,1100,1200);
  sky.addColorStop(0,'#171425');
  sky.addColorStop(.55,'#1f2144');
  sky.addColorStop(1,'#101228');
  ctx.fillStyle = sky;
  ctx.fillRect(0,0,1200,1200);
  const gold = '#f0cf91';
  ctx.strokeStyle = gold;
  ctx.lineWidth = 3;
  ctx.strokeRect(42,42,1116,1116);
  for (let i=0;i<64;i++) {
    ctx.globalAlpha = .15 + (i%5)*.09;
    ctx.fillStyle = gold;
    const x = 75+(i*319)%1051, y = 75+(i*i*43)%1051;
    ctx.fillRect(x,y,i%6===0 ? 5 : 2,i%6===0 ? 5 : 2);
  }
  ctx.globalAlpha = 1;
  const write = (value,x,y,size,color='#fff1d9',weight='700',family='Arial, sans-serif',direction='rtl') => {
    ctx.direction = direction;
    ctx.font = weight+' '+size+'px '+family;
    ctx.textAlign = 'center';
    ctx.fillStyle = color;
    ctx.fillText(value,x,y);
  };
  write('ישראל נט | אסטרולוגיה',600,156,41,gold);
  write('שלושת המזלות שלי',600,300,75);
  known.forEach((sign,index) => {
    const x=940-340*index;
    ctx.fillStyle='#292544';
    ctx.fillRect(x-143,400,286,391);
    ctx.strokeStyle='#9d7848';
    ctx.strokeRect(x-143,400,286,391);
    write(glyphs[sign]+'\uFE0E',x,566,116,gold,'400','system-ui, sans-serif','ltr');
    write(titles[index],x,658,41,'#e8d9be');
    write(signNames[sign],x,738,54);
  });
  write('ומה שלושת המזלות שלך?',600,951,49,gold);
  write('isnet.co.il/astrology',600,1030,34,'#fff1d9','400','Arial, sans-serif','ltr');
  return new Promise((resolve,reject) => canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('canvas')), 'image/png'));
}

function sharing(known) {
  const section = node('section',null,'rising-share');
  section.append(node('h3','לשתף את המחשבון'));
  const actions = node('div',null,'rising-share-actions');
  const status = node('p');
  status.setAttribute('aria-live','polite');
  const copy = node('button','העתקת קישור');
  copy.type = 'button';
  copy.addEventListener('click',async () => {
    try {
      await navigator.clipboard.writeText(canonical);
      status.textContent = 'הקישור הועתק.';
    } catch {
      const href = node('a',canonical);
      href.href = canonical;
      href.dir = 'ltr';
      status.replaceChildren('אפשר להעתיק את הקישור: ',href);
    }
  });
  actions.append(copy);
  if (known.every(sign => sign !== null)) {
    section.append(node('p','הכרטיס כולל רק את שמות המזלות. פרטי הלידה אינם מופיעים בו.'));
    const fileName = 'isnet-three-signs.png';
    const download = node('button','הורדת כרטיס PNG');
    download.type = 'button';
    download.addEventListener('click',async () => {
      try {
        const href = URL.createObjectURL(await shareImage(known));
        const link = node('a');
        link.href = href;
        link.download = fileName;
        document.body.append(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(href),30000);
        status.textContent = 'הכרטיס נוצר להורדה.';
      } catch { status.textContent = 'יצירת הכרטיס לא הצליחה. אפשר להעתיק את הקישור.'; }
    });
    actions.prepend(download);
    if (typeof navigator.share === 'function') {
      const share = node('button','שיתוף');
      share.type = 'button';
      // Prepare the image before the tap to keep Safari’s user activation.
      let shareFile;
      shareImage(known).then(blob => { shareFile = new File([blob],fileName,{type:'image/png'}); }).catch(() => {});
      share.addEventListener('click',async () => {
        const shareData = {title:'ומה שלושת המזלות שלך?',url:canonical};
        try {
          if (shareFile && navigator.canShare?.({files:[shareFile]})) shareData.files = [shareFile];
          await navigator.share(shareData);
        } catch (err) { if (err.name !== 'AbortError') status.textContent = 'השיתוף לא זמין כרגע. אפשר להוריד כרטיס או להעתיק קישור.'; }
      });
      actions.append(share);
    }
  } else if (typeof navigator.share === 'function') {
    const share = node('button','שיתוף קישור');
    share.type = 'button';
    share.addEventListener('click',() => navigator.share({title:'שלושת המזלות שלי',url:canonical}).catch(err => {
      if (err.name !== 'AbortError') status.textContent = 'השיתוף לא זמין כרגע. אפשר להעתיק את הקישור.';
    }));
    actions.append(share);
  }
  section.append(actions,status);
  return section;
}
