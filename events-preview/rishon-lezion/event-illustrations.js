// ISNET shared layout: edit events-preview/ashdod, not this generated file.
/* ISNET Ashdod: activity-specific illustrations, October 2026.
   This selects fallback media only; original event photographs take priority. */
(function(){
  const scriptUrl=document.currentScript.src;
  const base=new URL("assets/illustrations/v1/",scriptUrl);
  const nextBase=new URL("assets/illustrations/v2/",scriptUrl);
  window.isnetEventIllustration=function(e){
    if(!e)return null;
    const title=String(e.title||"");
    const sub=String(e.subcategory||"");
    const cat=String(e.category||"");
    let name="",label="",version=1;
    if(sub==="story-time"||/שעת סיפור/.test(title)){
      name="story-time";label="שעת סיפור";
    }else if((cat==="kids"||/ילדים|לילדים/.test(title)) &&
      (/יצירה|ציור|קרמיקה|פיסול|מלאכת יד/.test(title)||sub==="kids-workshops")){
      name="kids-creative";label="יצירה לילדים";
    }else if((cat==="lecture"||sub==="senior-lectures"||sub==="lecture")&&!/יריד|סדנ|סיור/.test(title)){
      name="lecture";label="הרצאות והעשרה";
    }else if(cat==="music"&&/אקוסטי|אינטימי|acoustic/i.test(title)){
      name="acoustic-music";label="מוזיקה אקוסטית";
    }
    if(!name){
      if(cat==="kids"&&(/המרחב הבטוח לילדים ולהורים|משחק חופשי/.test(title))){
        name="parent-child-play";label="פעילות הורים וילדים";version=2;
      }else if(cat!=="kids"&&/ציור|ציור אינטואיטיבי/.test(title)&&!/בוטני|ילדים|לילדים/.test(title)){
        name="adult-painting";label="ציור למבוגרים";version=2;
      }else if(cat==="exhibition"&&/תערוכ|גלריה|סיור.*מוזיאון/.test(title)&&!/סדנ|יצירה|קורס/.test(title)){
        name="art-gallery";label="ביקור בתערוכה";version=2;
      }else if(cat==="standup"){
        name="standup-stage";label="סטנדאפ";version=2;
      }
    }
    return name?{src:new URL(name+".webp",version===2?nextBase:base).href,label}:null;
  };
})();
