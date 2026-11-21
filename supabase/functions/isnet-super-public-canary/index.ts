// Narrow anonymous shadow canary. NOT a replacement for ISNET city URLs.
// Exposes only the already-public, unchanged 2026-11-10 Yavne price JSON.
// Never exposes Storage keys, media, source diagnostics or newer-than-proven prices.
// Disable immediately using supabase/functions/isnet-super-public-canary/rollback.ts.
const PROJECT = "qomkxhafrprooekwgsxf";
const BUCKET = "isnet-super-staging";
const RELEASE = "5958cfaca9a61eacfdb1aa216635c3d3ff810850";
const EXPECTED_SHA256 = "d0b3ffc01047f89bc08d34f652dc61de27cb16e4356db689594b2f824223072c";
const SNAPSHOT = "2026-11-10T10:40:34.858582+02:00";
const MAX_BYTES = 64 * 1024;
const ROOT = "releases/YAVNE/" + RELEASE + "/";
const PRICE_PATH = "SUPER.YAVNE/data/prices.json";
const ENDPOINT = "https://" + PROJECT + ".supabase.co/storage/v1/object/authenticated/" + BUCKET + "/";
const HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Expose-Headers": "ETag, X-Isnet-Preview-Only, X-Isnet-Snapshot-At, X-Isnet-SHA256",
  "Cache-Control": "no-store, max-age=0",
  "X-Robots-Tag": "noindex, nofollow, noarchive",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
};
function answer(status: number, error: string): Response {
  return new Response(JSON.stringify({ error, preview_only: true }), {
    status, headers: { ...HEADERS, "Content-Type": "application/json; charset=utf-8" },
  });
}
async function readPrivate(path: string, key: string): Promise<ArrayBuffer> {
  const res = await fetch(ENDPOINT + path, {
    headers: { apikey: key, authorization: "Bearer " + key },
    redirect: "error", signal: AbortSignal.timeout(9000),
  });
  if (!res.ok) throw Error("Private read status " + res.status);
  const len = Number(res.headers.get("content-length"));
  if (len > MAX_BYTES) throw Error("Object size limit");
  const data = await res.arrayBuffer();
  if (data.byteLength === 0 || data.byteLength > MAX_BYTES) throw Error("Object byte limit");
  return data;
}
async function digest(data: ArrayBuffer): Promise<string> {
  return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", data)))
    .map(n => n.toString(16).padStart(2, "0")).join("");
}
Deno.serve(async request => {
  if (request.method === "OPTIONS") return new Response(null, {
    status: 204, headers: { ...HEADERS, "Access-Control-Allow-Headers": "Content-Type" },
  });
  if (request.method !== "GET") return answer(405, "GET only");
  const u = new URL(request.url);
  if (!u.pathname.endsWith("/isnet-super-public-canary") ||
      u.searchParams.size !== 3 ||
      u.searchParams.getAll("city").length !== 1 ||
      u.searchParams.getAll("file").length !== 1 ||
      u.searchParams.getAll("release").length !== 1 ||
      u.searchParams.get("city") !== "YAVNE" ||
      u.searchParams.get("file") !== "prices.json" ||
      u.searchParams.get("release") !== RELEASE) {
    return answer(404, "Canary route not allowed");
  }
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!key) return answer(503, "Canary unavailable");
  try {
    const manifestBytes = await readPrivate(ROOT + "release-manifest.json", key);
    const manifest = JSON.parse(new TextDecoder().decode(manifestBytes));
    if (manifest.city !== "YAVNE" || manifest.release !== RELEASE ||
        manifest.public_cutover !== false || manifest.private !== true ||
        !Array.isArray(manifest.files)) throw Error("Manifest mismatch");
    const matching = manifest.files.filter((entry: {path?: string}) =>
      entry.path === PRICE_PATH);
    if (matching.length !== 1 || matching[0].sha256 !== EXPECTED_SHA256 ||
        !Number.isInteger(matching[0].bytes) ||
        matching[0].bytes < 1 || matching[0].bytes > MAX_BYTES)
      throw Error("Pinned manifest SHA256 mismatch");
    const data = await readPrivate(ROOT + PRICE_PATH, key);
    if (data.byteLength !== matching[0].bytes ||
        await digest(data) !== EXPECTED_SHA256) throw Error("Payload mismatch");
    const parsed = JSON.parse(new TextDecoder().decode(data));
    if (parsed.retrieved_at !== SNAPSHOT || parsed.branch_count !== 7)
      throw Error("Pinned freshness/source mismatch");
    return new Response(data, {
      status: 200,
      headers: {
        ...HEADERS, "Content-Type": "application/json; charset=utf-8",
        ETag: '"' + EXPECTED_SHA256 + '"',
        "X-Isnet-Preview-Only": "true",
        "X-Isnet-Snapshot-At": SNAPSHOT,
        "X-Isnet-SHA256": EXPECTED_SHA256,
      },
    });
  } catch (error) {
    console.error("Shadow canary rejected unverified payload", String(error));
    return answer(503, "Pinned snapshot temporarily unavailable");
  }
});
