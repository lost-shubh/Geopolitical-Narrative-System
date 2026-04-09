type Status = "ok" | "degraded" | "failed" | string;

function statusClassName(status: Status) {
  const normalized = status.toLowerCase();

  if (normalized === "ok" || normalized.includes("positive")) {
    return "status-badge status-ok";
  }
  if (normalized === "degraded" || normalized.includes("neutral") || normalized.includes("mixed")) {
    return "status-badge status-degraded";
  }
  if (normalized === "failed" || normalized.includes("negative")) {
    return "status-badge status-failed";
  }
  return "status-badge status-unknown";
}

export function StatusBadge({ status }: { status: Status }) {
  return <span className={statusClassName(status)}>{status}</span>;
}
