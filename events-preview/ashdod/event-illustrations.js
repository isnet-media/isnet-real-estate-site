/* ISNET Ashdod: activity-specific illustrations, October 2026.
   This selects fallback media only; original event photographs take priority. */
(function(){
  const scriptUrl=document.currentScript.src;
  const base=new URL("assets/illustrations/v1/",scriptUrl);
  const nextBase=new URL("assets/illustrations/v2/",scriptUrl);
  const thirdBase=new URL("assets/illustrations/v3/",scriptUrl);
  window.isnetEventDefaultImage=function(e){return /(?:^|\/)defaults\//i.test(String(e?.image_url||""));};
  window.isnetEventIllustration=function(e){
    if(!e)return null;
    const title=String(e.title||"");
    const sub=String(e.subcategory||"");
    const cat=String(e.category||"");
    let name="",label="",version=1;
    if(/קריאה|הקרא/.test(title)&&/כלב/.test(title)){
      name="reading-with-dog";label="קריאה בעזרת כלבים";version=3;
    }else if(cat==="kids"&&/כתיבה/.test(title)){
      name="kids-writing";label="כתיבה לילדים";version=3;
    }else if(cat!=="kids"&&/סדנ.*כתיבה|מפגשי כתיבה|כותבות אהבה/.test(title)){
      name="adult-writing";label="כתיבה יוצרת";version=3;
    }else if(["workshop","seniors","community"].includes(cat)&&/רשתות חברתיות|טיפים בנייד|בינה מלאכותית|קורס קנווה|סמארטפון|מחשבים|דיגיטל/.test(title)){
      name="digital-learning";label="למידה דיגיטלית";version=3;
    }else if(sub==="story-time"||/שעת סיפור/.test(title)){
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
    return name?{src:new URL(name+".webp",version===3?thirdBase:(version===2?nextBase:base)).href,label}:null;
  };
})();
