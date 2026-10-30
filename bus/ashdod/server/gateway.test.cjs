const test=require('node:test');
const assert=require('node:assert/strict');
const G=require('./gateway.cjs');
test('rejects invalid coordinates',()=>{
 assert.equal(G.validPoint({lat:31.8,lon:34.6}),true);
 assert.equal(G.validPoint({lat:91,lon:34.6}),false);
 assert.equal(G.validPoint({lat:31.8,lon:'34.6'}),false);
});
test('decodes Valhalla polyline6',()=>{
 // Zero delta encoded as '?' for each component.
 assert.deepEqual(G.decodePolyline6('????'),[{lat:0,lon:0},{lat:0,lon:0}]);
 assert.throws(()=>G.decodePolyline6('?'));
});
test('geocoder rejects missing house number and mismatched house number',()=>{
 const sample={lat:'31.8',lon:'34.6',display_name:'מיכאל אנג\'לו 11, אשדוד',address:{house_number:'11',city:'אשדוד'}};
 assert.equal(G.parseGeocode([sample],'מיכאל אנג\'לו 9').length,0);
 assert.equal(G.parseGeocode([sample],'מיכאל אנג\'לו 11').length,1);
 assert.equal(G.parseGeocode([{...sample,address:{city:'אשדוד'}}],'מיכאל אנג\'לו 11').length,0);
});
