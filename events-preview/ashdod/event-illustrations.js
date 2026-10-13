/* ISNET Ashdod: activity-specific illustrations, October 2026.
   This selects fallback media only; original event photographs take priority. */
(function(){
  const scriptUrl=document.currentScript.src;
  const base=new URL("assets/illustrations/v1/",scriptUrl);
  window.isnetEventIllustration=function(e){
    if(!e)return null;
    const title=String(e.title||"");
    const sub=String(e.subcategory||"");
    const cat=String(e.category||"");
    let name="",label="";
    if(sub==="story-time"||/שעת סיפור/.test(title)){
      name="story-time";label="שעת סיפור";
    }else if((cat==="kids"||/ילדים|לילדים/.test(title)) &&
      (/יצירה|ציור|קרמיקה|פיסול|מלאכת יד/.test(title)||sub==="kids-workshops")){
      name="kids-creative";label="יצירה לילדים";
    }else if(cat==="lecture"||sub==="senior-lectures"||sub==="lecture"){
      name="lecture";label="הרצאות והעשרה";
    }else if(cat==="music"&&/אקוסטי|אינטימי|acoustic/i.test(title)){
      name="acoustic-music";label="מוזיקה אקוסטית";
    }
    return name?{src:new URL(name+".webp",base).href,label}:null;
  };
})();
