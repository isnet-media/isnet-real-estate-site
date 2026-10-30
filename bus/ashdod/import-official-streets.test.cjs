const test=require('node:test'),assert=require('node:assert/strict');const {parseCSV,extract}=require('./import-official-streets.cjs');
test('CSV supports quoted commas and Hebrew',()=>assert.deepEqual(parseCSV('שם_רחוב,שם_ישוב\n"גן, העיר",אשדוד\n')[1],['גן, העיר','אשדוד']));
test('filter to Ashdod and preserve official identifiers',()=>{
 const csv='סמל_ישוב,שם_ישוב,סמל_רחוב,שם_רחוב\n70,אשדוד,101,שדרות בני ברית\n70,אשדוד,102,הגדוד העברי\n999,חיפה,101,הרצל\n';
 const result=extract(csv);assert.equal(result.length,2);assert.equal(result[0].cityCode,'70');assert.equal(result.some(x=>x.name==='הרצל'),false);
});
test('reject entries missing street codes',()=>assert.equal(extract('סמל_ישוב,שם_ישוב,סמל_רחוב,שם_רחוב\n70,אשדוד,,לא ידוע\n').length,0));
