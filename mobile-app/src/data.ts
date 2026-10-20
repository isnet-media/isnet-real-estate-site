export const BASE='https://isnet.co.il/events-preview/ashdod/';
export type EventItem={event_id?:string;title?:string;series_title?:string;category?:string;subcategory?:string;start_date?:string;start_time?:string;image_url?:string;image?:string;ticket_url?:string;source_url?:string;description?:string;venue?:string};
export type Movie={id?:string;title?:string;poster_url?:string;trailer_url?:string};
const load=async(path:string)=>{const r=await fetch(BASE+path,{headers:{Accept:'application/json'}});if(!r.ok)throw Error('HTTP '+r.status);return r.json()};
export async function getEvents():Promise<EventItem[]>{const data=await load('data/events.json');return Array.isArray(data)?data:Array.isArray(data.events)?data.events:[]}
export async function getMovies():Promise<Movie[]>{const data=await load('data/cinema.json');return Array.isArray(data.movies)?data.movies:[]}
export const categories:Record<string,string>={music:'הופעות',standup:'סטנדאפ',theatre:'הצגות',kids:'ילדים ומשפחה',cinema:'קולנוע',lecture:'הרצאות',exhibition:'תערוכות',sport:'ספורט',community:'קהילה',seniors:'הגיל השלישי',festival:'פסטיבלים',food:'קולינריה'};
