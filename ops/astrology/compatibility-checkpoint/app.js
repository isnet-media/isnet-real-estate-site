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
