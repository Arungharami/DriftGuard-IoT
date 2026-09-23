import { infer } from "@/lib/inference";
export const runtime = "nodejs";
export async function POST(request: Request) {
  if (!request.headers.get("content-type")?.startsWith("application/json")) return Response.json({ error: "JSON required" }, { status: 415 });
  // Stream with a hard byte cap; never buffer an unbounded submitted body.
  const reader = request.body?.getReader();
  if (!reader) return Response.json({ error: "Body required" }, { status: 400 });
  let bytes = 0;
  const chunks: Uint8Array[] = [];
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    bytes += value.length;
    if (bytes > 32768) { await reader.cancel(); return Response.json({ error: "Request too large" }, { status: 413 }); }
    chunks.push(value);
  }
  let body: unknown;
  try { body = JSON.parse(Buffer.concat(chunks).toString("utf8")); }
  catch { return Response.json({ error: "Invalid JSON" }, { status: 400 }); }
  const result = await infer(body, process.env);
  return Response.json(result.body, { status: result.status, headers: { "Cache-Control": "no-store", ...(result.status === 429 ? { "Retry-After": "60" } : {}) } });
}
