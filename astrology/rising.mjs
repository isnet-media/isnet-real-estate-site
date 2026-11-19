const radians = Math.PI / 180;
const circle = value => (value % 360 + 360) % 360;

export function localInstants(date, time, zone) {
  const nominal = Date.parse(date + 'T' + time + ':00Z');
  if (!Number.isFinite(nominal)) return [];
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: zone, calendar: 'gregory', numberingSystem: 'latn', hourCycle: 'h23',
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit',
    minute: '2-digit', second: '2-digit'
  });
  const clock = timestamp => {
    const f = Object.fromEntries(formatter.formatToParts(timestamp).map(({type, value}) => [type, value]));
    return Date.parse(`${f.year}-${f.month}-${f.day}T${f.hour}:${f.minute}:${f.second}Z`);
  };
  const offsets = new Set([-48,-24,-12,0,12,24,48].map(hours => {
    const sample = nominal + hours * 3600000;
    return clock(sample) - sample;
  }));
  return [...offsets].map(offset => nominal - offset).filter(candidate => clock(candidate) === nominal);
}

export function risingLongitude(timestamp, latitude, longitude) {
  if (!Number.isFinite(timestamp) || !Number.isFinite(latitude) || Math.abs(latitude) >= 66.5 ||
      !Number.isFinite(longitude) || Math.abs(longitude) > 180) throw new RangeError('Invalid coordinates');
  const days = timestamp / 86400000 + 2440587.5 - 2451545;
  const centuries = days / 36525;
  const theta = circle(280.46061837 + 360.98564736629 * days + 0.000387933 *
    centuries ** 2 - centuries ** 3 / 38710000 + longitude) * radians;
  const tilt = (23.43929111 - 0.013004167 * centuries) * radians;
  return circle(Math.atan2(Math.cos(theta), -(Math.sin(theta) * Math.cos(tilt) +
    Math.tan(latitude * radians) * Math.sin(tilt))) / radians);
}

const readings = [
  ['טלה','ישירות ויוזמה','פתיחה מהירה יכולה להניע שיחה או משימה תקועה. בקשרים קרובים ובעבודה, השהיה קצרה מאפשרת גם לאחרים לבחור איך להצטרף.','לפני ההצעה הבאה, שאלו מה הצד השני היה רוצה שיקרה.'],
  ['שור','יציבות ונוכחות','רוגע ועקביות יכולים לשדר ביטחון גם בלי הרבה מילים. כשקצב הביצוע משתנה בעבודה או בבית, כדאי לברר מה חיוני לכם לשמר.','בחרו שינוי קטן שתוכלו לנסות בלי לוותר על שגרה שטובה לכם.'],
  ['תאומים','סקרנות וגמישות','שאלות מהירות עשויות לפתוח דלתות בשיחה ובצוות. בקשר מתמשך, הישארות עם נושא אחד עוד רגע יכולה ליצור תחושה שמישהו באמת נשמע.','בשיחה הבאה שאלו שאלת המשך לפני שתספרו סיפור משלכם.'],
  ['סרטן','רגישות לסביבה','אתם עשויים לשים לב מהר לאווירה ולמה שאנשים צריכים. בעבודה ובבית כדאי לומר גם מה אתם צריכים, כדי שהטיפול באחרים לא יהפוך לאחריות מובנת מאליה.','נסחו בקשה אחת שאפשר לענות עליה בצורה מעשית.'],
  ['אריה','חום ונראות','נוכחות פתוחה יכולה להקל על אנשים להתחיל לדבר או להצטרף לפרויקט. בקשרים ובעבודה, שיתוף הבמה עשוי להעמיק את האמון מעבר לרושם הראשון.','תנו למישהו נוסף לפתוח שיחה שאתם בדרך כלל מובילים.'],
  ['בתולה','דיוק והבחנה','היכולת להבחין בפרטים יכולה להרגיע צוות ולתת תמיכה מעשית בבית. לפעמים מה שנחוץ לצד השני הוא הקשבה לפני הצעת תיקון.','שאלו אם מתאים לקבל הצעה לפני שאתם נותנים אותה.'],
  ['מאזניים','התחשבות ושיקול דעת','קל לכם לראות כמה נקודות מבט, תכונה שמועילה בשיתוף פעולה ובזוגיות. הבעת העדפה ברורה יכולה אפילו להקל על החלטה משותפת.','אמרו מה הייתם בוחרים לפני שתציעו פשרה.'],
  ['עקרב','עומק ובירור','נוכחות שקטה וסקרנות לגבי מה שמסתתר מאחורי הדברים עשויות לבלוט מהר. בקשר קרוב או בעבודה, אפשר לבקש בהירות בלי להניח מראש כוונה.','הפכו השערה אחת לשאלה ישירה ומכבדת.'],
  ['קשת','פתיחות ואופק רחב','רעיון חדש או נקודת מבט אחרת יכולים להכניס אנרגיה למפגש ולצוות. בקשר מתמשך, כדאי לבדוק איך ההתלהבות נשמרת גם בפרטים הקטנים.','בחרו רעיון אחד והגדירו פעולה קטנה שתוכלו להשלים השבוע.'],
  ['גדי','אחריות ותכנון','היכולת לקחת דברים ברצינות עשויה להשרות אמון בעבודה ובבית. שיתוף בכוונה או בהתלבטות מוקדם יותר נותן לאחרים הזדמנות להיות שותפים.','בחרו משימה אחת שאפשר לחלוק, ובקשו עזרה לפני שהעומס גדל.'],
  ['דלי','עצמאות ומחשבה מקורית','מבט מעט אחר יכול לשנות שיחה או לפתור בעיה קבוצתית. ביחסים ובעבודה, הסבר אישי וקונקרטי עוזר לאחרים להבין מה חשוב לכם.','תארו כבעיה מעשית אחת את השינוי שאתם רוצים לראות.'],
  ['דגים','דמיון והקשבה','קליטת ניואנסים יכולה לעזור בשיחה ובעבודה יצירתית. לפני שאתם מקבלים על עצמכם עוד צורך של מישהו אחר, בררו מה התבקש ומה אתם יכולים לתת.','רשמו דבר אחד שאתם מרגישים ודבר אחד שאתם יודעים, והשוו ביניהם.']
];

const form = typeof document === 'undefined' ? null : document.querySelector('#rising-form');
if (form) {
  const fields = form.elements;
  const custom = document.querySelector('#rising-custom');
  const result = document.querySelector('#rising-result');
  form.addEventListener('change', () => { custom.hidden = fields.city.value !== 'custom'; });
  form.addEventListener('submit', event => {
    event.preventDefault();
    result.replaceChildren();
    result.hidden = false;
    const print = (tag, message) => {
      const node = document.createElement(tag);
      node.textContent = message;
      result.append(node);
    };
    if (!fields.day.value || !fields.hour.value) {
      print('p', 'לחישוב אופק דרושים תאריך ושעת לידה מקומית. אם שעת הלידה אינה ידועה, אין דרך לתת מזל אופק מדויק.');
      return;
    }
    const values = fields.city.value === 'custom' ?
      [fields.lat.value, fields.lon.value, fields.zone.value.trim()] : fields.city.value.split(',');
    if (values.some(value => value === '')) {
      print('p','בחרו מקום לידה או מלאו קווי רוחב ואורך ואזור זמן.');
      return;
    }
    const [lat, lon, zone] = values;
    let instants;
    try { instants = localInstants(fields.day.value, fields.hour.value, zone); }
    catch { print('p','אזור הזמן אינו מוכר. הזינו מזהה כמו Europe/Paris.'); return; }
    if (instants.length !== 1) {
      print('p', instants.length ? 'השעה הופיעה פעמיים בגלל מעבר שעון. צריך לזהות באיזו מהן התרחשה הלידה.' :
        'השעה המקומית אינה קיימת בתאריך הזה לפי כללי אזור הזמן. בדקו את פרטי הלידה.');
      return;
    }
    let degree;
    try { degree = risingLongitude(instants[0],Number(lat),Number(lon)); }
    catch { print('p','בדקו את הקואורדינטות. החישוב הזמין כאן מוגבל לקווי רוחב בין 66.5° דרום ל־66.5° צפון.'); return; }
    const [name, theme, interpretation, practice] = readings[Math.floor(degree / 30)];
    const within = degree % 30;
    print('h2', 'אופק ' + name);
    print('p', `מיקום משוער במזל: ${within.toFixed(2)}° · ${theme}`);
    if (within < 0.5 || within > 29.5) print('p','האופק קרוב לגבול בין מזלות. סטייה קטנה בשעת הלידה עשויה לשנות את התוצאה.');
    print('h3','קריאה אסטרולוגית להתבוננות');
    print('p',interpretation);
    print('h3','צעד מעשי');
    print('p',practice);
  });
}
