const result = document.querySelector('#result');

function show(title, lines) {
  const heading = document.createElement('h2');
  heading.textContent = title;
  const paragraphs = lines.map(line => {
    const paragraph = document.createElement('p');
    paragraph.textContent = line;
    return paragraph;
  });
  result.replaceChildren(heading, ...paragraphs);
  result.hidden = false;
}

const match = document.querySelector('#match');
if (match) {
  const first = document.querySelector('#first');
  const second = document.querySelector('#second');
  second.selectedIndex = 1;
  const prompts = {
    אש: 'מה הייתם רוצים ליזום יחד, ואיך תתנו לכל אחד זמן להחליט?',
    אדמה: 'איזה הרגל משותף נוח לשניכם, ואיפה כדאי להשאיר מקום לספונטניות?',
    אוויר: 'מה מסקרן את שניכם, ואיך תעברו משיחה לתוכנית משותפת?',
    מים: 'איזה סוג של תמיכה כל אחד מבקש כשעובר עליו יום עמוס?'
  };
  const signs = fetch('/astrology/signs.json').then(response => {
    if (!response.ok) throw new Error('Sign data unavailable');
    return response.json();
  });
  signs.then(rows => {
    const slug = new URLSearchParams(location.search).get('sign');
    const index = rows.findIndex(row => row[0] === slug);
    if (index >= 0) first.selectedIndex = index;
  }).catch(() => {});
  match.addEventListener('submit', async event => {
    event.preventDefault();
    try {
      const rows = await signs;
      const pair = [rows[first.selectedIndex][0], rows[second.selectedIndex][0]].sort().join('-');
      if (pair === 'capricorn-virgo') {
        location.assign('/astrology/compatibility/capricorn-virgo/');
        return;
      }
      const [, a,, elementA] = rows[first.selectedIndex];
      const [, b,, elementB] = rows[second.selectedIndex];
      const shared = elementA === elementB;
      show(a + ' ו' + b, [
        'במסורת האסטרולוגית, ' + a + ' שייך ליסוד ' + elementA + ' ו' + b + ' ליסוד ' + elementB + '.',
        shared ? 'יסוד משותף מזמין לבדוק היכן אתם מגיבים באופן דומה, ומתי כל אחד זקוק למשהו אחר.' : 'יסודות שונים מזמינים לבדוק איך כל אחד מביא לקשר קצב וצורת תקשורת משלו.',
        ...new Set([prompts[elementA], prompts[elementB]])
      ]);
    } catch {
      show('הנתונים אינם זמינים כרגע', ['אפשר לטעון מחדש את העמוד ולנסות שוב.']);
    }
  });
}

const compass = document.querySelector('#compass');
if (compass) {
  const exercises = [
    ['איזה הרגל אני רוצה לשנות השבוע?', 'בחרו פעולה של שתי דקות וקבעו מתי תעשו אותה בפעם הראשונה.'],
    ['איזו שיחה חשובה אני דוחה?', 'נסחו משפט פתיחה שמתאר את מה שאתם מרגישים ואת מה שאתם מבקשים.'],
    ['איזו משימה תעזור לי להתקדם השבוע?', 'הקצו לה זמן ביומן וקבעו מה ייחשב לתוצאה מספיקה.']
  ];
  compass.addEventListener('submit', event => {
    event.preventDefault();
    show('תרגיל לשבוע הקרוב', exercises[document.querySelector('#topic').selectedIndex]);
  });
}
