(function(root){
 'use strict';
 const limit=100;
 function clean(values){return [...new Set((Array.isArray(values)?values:[]).filter(x=>typeof x==='string'&&/^[a-zA-Z0-9_-]{1,150}$/.test(x)))].slice(0,limit)}
 function decode(hash){try{const value=new URLSearchParams(String(hash||'').replace(/^#/, '')).get('saved');return value?clean(JSON.parse(value)):null}catch{return null}}
 function link(address,ids){const values=clean(ids);if(!values.length)throw new Error('EMPTY_LIST');if(ids.length>limit)throw new Error('LIST_TOO_LONG');const url=new URL(address);url.search='';url.hash=new URLSearchParams({saved:JSON.stringify(values)}).toString();return url.href}
 const api={clean,decode,link,limit};root.ISNET_SAVED_LIST=api;if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window==='object'?window:globalThis);
