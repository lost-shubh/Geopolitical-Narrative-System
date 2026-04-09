import { NextResponse } from "next/server";
import { loadSnapshotEnvelope } from "@/src/lib/blob-snapshot";

export const dynamic = "force-dynamic";

export async function GET() {
  const envelope = await loadSnapshotEnvelope();
  return NextResponse.json(envelope, {
    headers: {
      "Cache-Control": "no-store, max-age=0",
    },
  });
}
