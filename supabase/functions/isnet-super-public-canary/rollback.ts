// Emergency fail-closed redeploy for the nonproduction public canary.
// No DNS, storage, collector or existing live city route is changed.
Deno.serve(() => new Response(
  JSON.stringify({ error: "Canary disabled", preview_only: true }),
  { status: 503, headers: {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": "no-store, max-age=0",
    "X-Robots-Tag": "noindex, nofollow, noarchive",
    "X-Content-Type-Options": "nosniff",
  }}
));
