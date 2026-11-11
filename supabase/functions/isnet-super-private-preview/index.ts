// ISNET: private read-only delivery rehearsal. NOT a public supermarket endpoint.
// Runtime gateway requires a verified JWT; handler additionally requires the
// exact server-side service role key. NEVER embed this key in a webpage or app.
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
const FILES = new Set(["prices.json", "refresh-status.json", "source-status.json"]);
const MAX_BYTES = 96 * 1024;
const NO_CACHE: HeadersInit = {
  "Cache-Control": "private, no-store, max-age=0",
  "X-Robots-Tag": "noindex, nofollow, noarchive",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
};
function response(status: number, message: string): Response {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { ...NO_CACHE, "Content-Type": "application/json; charset=utf-8" },
  });
}
async function sha256Hex(buf: ArrayBuffer): Promise<string> {
  const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", buf));
  return [...hash].map(x => x.toString(16).padStart(2, "0")).join("");
}
async function storageRead(path: string, key: string): Promise<ArrayBuffer> {
  // path is assembled ONLY from fixed allowlists, never user-supplied URL segments.
  const url = BASE + "/storage/v1/object/authenticated/" + BUCKET + "/" + path;
  const remote = await fetch(url, {
    method: "GET",
    headers: { "Authorization": "Bearer " + key, "apikey": key },
    redirect: "error",
    signal: AbortSignal.timeout(10000),
  });
  if (!remote.ok) throw new Error("Private Storage read failed " + remote.status);
  const size = Number(remote.headers.get("content-length"));
  if (size > MAX_BYTES) throw new Error("Object is too large for private preview");
  const body = await remote.arrayBuffer();
  if (body.byteLength > MAX_BYTES) throw new Error("Private preview size exceeded");
  return body;
}
Deno.serve(async (request) => {
  if (request.method !== "GET") return response(405, "Read-only GET required");
  const secret = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const url = new URL(request.url);
  const provided = request.headers.get("authorization");
  // This endpoint is a nonpublic staging preview, not a user-facing origin.
  if (!secret || provided !== "Bearer " + secret) return response(403, "Forbidden");
  if (url.searchParams.size !== 2 ||
      url.searchParams.getAll("city").length !== 1 ||
      url.searchParams.getAll("file").length !== 1)
    return response(400, "Invalid parameters");
  const city = url.searchParams.get("city") || "";
  const file = url.searchParams.get("file") || "";
  const release = RELEASES[city];
  if (!Object.hasOwn(RELEASES, city) || !release || !FILES.has(file))
    return response(400, "Unsupported release");
  const root = "releases/" + city + "/" + release + "/SUPER." + city + "/data/";
  try {
    const manifestBytes = await storageRead("releases/" + city + "/" + release + "/release-manifest.json", secret);
    const manifest = JSON.parse(new TextDecoder().decode(manifestBytes));
    if (manifest.city !== city || manifest.release !== release ||
        manifest.private !== true || manifest.public_cutover !== false ||
        !Array.isArray(manifest.files))
      throw new Error("Manifest release identity invalid");
    const path = "SUPER." + city + "/data/" + file;
    const entries = manifest.files.filter((item: {path?: string}) => item.path === path);
    if (entries.length !== 1 || !Number.isInteger(entries[0].bytes) ||
        entries[0].bytes < 1 || entries[0].bytes > MAX_BYTES ||
        !/^[a-f0-9]{64}$/.test(entries[0].sha256))
      throw new Error("Manifest file missing, oversized, or inconsistent");
    const body = await storageRead(root + file, secret);
    const hash = await sha256Hex(body);
    if (body.byteLength !== entries[0].bytes || hash !== entries[0].sha256)
      throw new Error("Storage read SHA256 mismatch");
    JSON.parse(new TextDecoder().decode(body)); // never silently publish malformed JSON
    return new Response(body, {
      status: 200,
      headers: {
        ...NO_CACHE,
        "Content-Type": "application/json; charset=utf-8",
        "ETag": '"' + hash + '"',
        "X-Isnet-Source-Release": release,
        "X-Isnet-Preview-Only": "true",
      },
    });
  } catch (err) {
    console.error("Private supermarket preview failed", String(err));
    return response(503, "Private release not currently verifiable");
  }
});
