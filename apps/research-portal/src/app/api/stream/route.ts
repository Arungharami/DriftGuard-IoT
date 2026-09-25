import { readStream } from "@/lib/streaming";

export const dynamic = "force-dynamic";
export async function GET() {
  const snapshot = await readStream(process.env);
  return Response.json(snapshot ?? { error: "Streaming backend unavailable" }, {
    status: snapshot ? 200 : 503,
    headers: { "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" },
  });
}
