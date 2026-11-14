// Authenticated shadow file-delivery probe; NEVER public hosting or a new price source.
// Source snapshots are pinned, immutable, private, and cross-checked against their manifests.
// No browser CORS, no HTML execution, no media/font delivery, no DNS or live route changes.
const PROJECT = "qomkxhafrprooekwgsxf";
const BASE = "https://" + PROJECT + ".supabase.co";
const BUCKET = "isnet-super-staging";
const RELEASES: Record<string, string> = {
  ASHDOD: "5958cfaca9a61eacfdb1aa216635c3d3ff810850",
  BATYAM: "5958cfaca9a61eacfdb1aa216635c3d3ff810850",
  HOLON: "5958cfaca9a61eacfdb1aa216635c3d3ff810850",
  KGAT: "5958cfaca9a61eacfdb1aa216635c3d3ff810850",
  RISHON: "5958cfaca9a61eacfdb1aa216635c3d3ff810850",
  YAVNE: "5958cfaca9a61eacfdb1aa216635c3d3ff810850",
  TLV: "c674f83485453570106ce39a55c9c66f3a061ec3",
};
const TYPES: Record<string, string> = {
  html: "text/html; charset=utf-8",
  css: "text/css; charset=utf-8",
  js: "application/javascript; charset=utf-8",
  json: "application/json; charset=utf-8",
};
const MAX_FILE = 12 * 1024 * 1024;
const MAX_MANIFEST = 512 * 1024;
const PROTECT = {
  "Cache-Control": "private, no-store, max-age=0",
  "X-Robots-Tag": "noindex, nofollow, noarchive",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; sandbox",
  "Cross-Origin-Resource-Policy": "same-origin",
};
function denied(status: number, error: string): Response {
  return new Response(JSON.stringify({error,preview_only:true}), {
    status, headers: {...PROTECT,"Content-Type":"application/json; charset=utf-8"},
  });
}
function checkedPath(raw: string): string | null {
  if (!raw || raw.length > 170 || !/^[a-zA-Z0-9_.\/-]+$/.test(raw)) return null;
  if (raw.startsWith("/") || raw.includes("//") || raw.split("/").some(s => s==="." || s===".." || !s)) return null;
  if (!Object.hasOwn(TYPES,raw.split(".").pop() || "")) return null;
  return raw;
}
async function readPrivate(path: string, key: string, max: number): Promise<ArrayBuffer> {
  const url=BASE+"/storage/v1/object/authenticated/"+BUCKET+"/"+path;
  const result=await fetch(url,{
    method:"GET", headers:{apikey:key, Authorization:"Bearer "+key},
    redirect:"error", signal:AbortSignal.timeout(12000),
  });
  if (!result.ok) throw new Error("Storage read HTTP "+result.status);
  const length=result.headers.get("Content-Length");
  if (length && Number(length) > max) throw new Error("Storage object exceeded maximum");
  const data=await result.arrayBuffer();
  if (data.byteLength > max) throw new Error("Storage object too large");
  return data;
}
async function digest(data: ArrayBuffer): Promise<string> {
  const hash=new Uint8Array(await crypto.subtle.digest("SHA-256",data));
  return Array.from(hash,x=>x.toString(16).padStart(2,"0")).join("");
}
Deno.serve(async(req) => {
  if (req.method!=="GET") return denied(405,"Only GET is permitted");
  const key=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!key || req.headers.get("authorization") !== "Bearer "+key) return denied(403,"Forbidden");
  const query=new URL(req.url).searchParams;
  if (query.size!==2 || query.getAll("city").length!==1 || query.getAll("path").length!==1)
    return denied(400,"Expected one city and one path");
  const city=query.get("city") || "";
  const rel=checkedPath(query.get("path") || "");
  if (!Object.hasOwn(RELEASES,city) || !rel) return denied(400,"Not an allowed release path");
  const release=RELEASES[city];
  const full="SUPER."+city+"/"+rel;
  try {
    const manifestBytes=await readPrivate("releases/"+city+"/"+release+"/release-manifest.json",key,MAX_MANIFEST);
    const m=JSON.parse(new TextDecoder().decode(manifestBytes));
    if (m.city!==city || m.release!==release || m.private!==true || m.public_cutover!==false || !Array.isArray(m.files))
      throw new Error("Untrusted release manifest");
    const matching=m.files.filter((f: {path?:string})=>f.path===full);
    if (matching.length!==1 || !Number.isInteger(matching[0].bytes) || matching[0].bytes<1 ||
        matching[0].bytes>MAX_FILE || !/^[a-f0-9]{64}$/.test(matching[0].sha256))
      throw new Error("Missing manifest entry");
    const data=await readPrivate("releases/"+city+"/"+release+"/"+full,key,MAX_FILE);
    const checksum=await digest(data);
    if (data.byteLength!==matching[0].bytes || checksum!==matching[0].sha256)
      throw new Error("SHA256 or file length mismatch");
    const ext=rel.split(".").pop() || "";
    if (ext==="json") JSON.parse(new TextDecoder().decode(data));
    return new Response(data,{status:200,headers:{
      ...PROTECT, "Content-Type":TYPES[ext],
      "Content-Disposition":'attachment; filename="super-preview.'+ext+'"',
      "ETag":'"'+checksum+'"',
      "X-Isnet-Preview-Only":"true",
      "X-Isnet-Pinned-Release":release
    }});
  } catch(err) {
    console.error("Fail-closed ISNET private site preview",String(err));
    return denied(503,"Pinned private file could not be verified");
  }
});
