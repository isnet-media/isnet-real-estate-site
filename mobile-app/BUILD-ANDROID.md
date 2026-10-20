# הפעלת גרסת ניסיון לאנדרואיד

הקוד נמצא בנתיב `mobile-app/` בענף `feature/ashdod-mobile-app-pilot`.

## בדיקה אוטומטית
GitHub Actions > Ashdod mobile validation > Run workflow.
בדיקת TypeScript והגדרות Expo רצה גם בעת עדכון קוד בענף.

## הפקת APK
1. ליצור או לחבר חשבון Expo בעל גישה לפרויקט.
2. להוסיף סוד מאגר בשם `EXPO_TOKEN` (GitHub > Settings > Secrets and variables > Actions).
3. להגדיר פרויקט Expo EAS פעם אחת בסביבת פיתוח: `cd mobile-app && npm install && npx eas-cli init`.
4. לשמור את `extra.eas.projectId` שייווצר ב-`app.json` בענף הפיתוח.
5. להריץ ידנית את workflow בענף הפיתוח. עבודת `android-preview` תשלח בניית APK לענן Expo.
6. לבדוק את תוצאת הבנייה ב-Expo, להוריד APK רק ממקור מאומת, ולהתקין במכשיר בדיקה.

אין להכניס טוקן לקוד או להודעות צ'אט. פרסום בחנויות דורש בדיקות נוספות.

## מגבלות ידועות
- חיבור JSON מוגדר אך טרם אומת במכשיר.
- כרטיסי האירועים ותמונות הקולנוע עדיין בסיסיים.
- נדרשת בדיקת התאמה למבנה אירועים בפועל, בדיקות RTL ובדיקת קישורים.
- בניית APK לא הופעלה או אומתה בעת יצירת מסמך זה.
