// ISNET shared layout: edit events-preview/ashdod, not this generated file.
/* ISNET Ashdod: activity-specific illustrations, October 2026.
   This selects fallback media only; original event photographs take priority. */
(function(){
  const scriptUrl=document.currentScript.src;
  const base=new URL("assets/illustrations/v1/",scriptUrl);
  const nextBase=new URL("assets/illustrations/v2/",scriptUrl);
  const thirdBase=new URL("assets/illustrations/v3/",scriptUrl);
  const fourthBase=new URL("assets/illustrations/v4/",scriptUrl);
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
    if(!name){
      const text=title+" "+String(e.description||"");
      const branch=[sub,e.sport_branch,e.sport,e.event_id].join(" ");
      if(/מועדון קריאה/.test(title)){name="book-club";label="מועדון קריאה";}
      else if(/חלוקי נחל/.test(title)){name="stone-painting";label="ציור על חלוקי נחל";}
      else if(/סרוג|סריגה|סרוגים/.test(title)){name="crochet";label="סריגה";}
      else if(/דרבוקה|מתופפ/.test(title)){name="drumming";label="תיפוף";}
      else if(/עוגות|בנטו/.test(title)){name="cake-decorating";label="עיצוב עוגות";}
      else if(/לחמניות|לחם|אפייה/.test(title)){name="bread-baking";label="אפייה";}
      else if(/על כיסא/.test(title)){name="chair-exercise";label="התעמלות על כיסא";}
      else if(/בודי בלט|בונה עצם|יריד בריאות/.test(title)){name="gentle-fitness";label="תנועה ואורח חיים";}
      else if(/ריקודי עם/.test(title)){name="folk-dance";label="ריקודי עם";}
      else if(/פלמנקו|flamenco/i.test(title)){name="flamenco";label="פלמנקו";}
      else if(/בלט|הרקדן/.test(title)){name="ballet-dance";label="בלט ומחול";}
      else if(/קאנבה|קנווה|חופשה בקליק/.test(title)){
        return {src:new URL("digital-learning.webp",thirdBase).href,label:"למידה דיגיטלית"};
      }
      else if(/סיפור יצירה/.test(title)||(/הורים.*ילדים/.test(title)&&/סדנ|מצייר|ציור/.test(title))){
        return {src:new URL("kids-creative.webp",base).href,label:"יצירה לילדים"};
      }
      else if(/רינת מטיילת|רינתי|נתי הגעתי/.test(title)){name="children-theatre";label="מופע לילדים";}
      else if(/ילד פלא/.test(title)&&/גדולות מהחיים/.test(title)){name="live-music";label="מופע מוזיקה";}
      else if(/סטנדאפ/.test(title)){
        return {src:new URL("standup-stage.webp",nextBase).href,label:"סטנדאפ"};
      }
      else if(/הרצאות|הרצאה|נמרולוג|נומרולוג|כח המילים|כוח המילים/.test(title)){
        return {src:new URL("lecture.webp",base).href,label:"הרצאות והעשרה"};
      }
      else if(/נקודת מפגש|פלשת|ארכיאולוג/.test(text)&&cat==="exhibition"){name="history-museum";label="מוזיאון והיסטוריה";}
      else if(/מוצאים עוגן|דקה לנשום|אני הרבה יותר|מאמא דייאלי/.test(title)){name="wellbeing-circle";label="מפגש חברתי";}
      else if(/FATE.*FIRE|CON TEH PARTIRO/.test(title)){
        return {src:new URL("assets/featured-stage/orchestra_conductor_golden_hall__carousel_640x480.webp",scriptUrl).href,label:"קונצרט"};
      }
      else if(/השועל המוסיקלי|טריפונס/.test(title)){name="live-music";label="מופע מוזיקה";}
      else if(cat==="sport"){
        if(/volleyball|כדורעף/.test(branch)){name="volleyball";label="כדורעף";}
        else if(/handball|כדוריד/.test(branch)){name="handball";label="כדוריד";}
        else if(/basketball|כדורסל/.test(branch)){name="basketball";label="כדורסל";}
        else if(/football|כדורגל/.test(branch)){name="football";label="כדורגל";}
        else{name="gentle-fitness";label="פעילות גופנית";}
      }
      else if(cat==="music"){name="live-music";label="מופע מוזיקה";}
      else if(cat==="theatre"){name="theatre-stage";label="תיאטרון";}
      else if(cat==="kids"){name="children-theatre";label="מופע לילדים";}
      else if(cat==="workshop"||/סטודיו פתוח|עיסת נייר/.test(title)){name="adult-crafts";label="יצירה";}
      else if(cat==="exhibition"){
        return {src:new URL("art-gallery.webp",nextBase).href,label:"תערוכה"};
      }
      else if(cat==="community"){
        const venue=String(e.venue||e.venue_name||"");
        name=/משכן|אולם|דיונה|מונארט/.test(venue)?"theatre-stage":"wellbeing-circle";
        label=name==="theatre-stage"?"אירוע במה":"מפגש קהילתי";
      }
      if(name)version=4;
    }
    return name?{src:new URL(name+".webp",version===4?fourthBase:(version===3?thirdBase:(version===2?nextBase:base))).href,label}:null;
  };
})();
