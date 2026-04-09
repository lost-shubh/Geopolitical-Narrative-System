import { DashboardShell } from "@/components/dashboard-shell";
import { loadSnapshotEnvelope } from "@/src/lib/blob-snapshot";

export default async function HomePage() {
  const envelope = await loadSnapshotEnvelope();
  return <DashboardShell initialEnvelope={envelope} />;
}
