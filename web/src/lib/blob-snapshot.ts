import { head } from "@vercel/blob";
import { mockSnapshot } from "@/src/lib/mock-snapshot";
import type { DeepSentimentSummary, HeadlineRecord, LiveSnapshot, LiveSnapshotEnvelope } from "@/src/lib/types";

const DEFAULT_PATH = "dashboard/live/latest.json";

function asNumber(value: unknown, fallback = 0) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function asString(value: unknown, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function normalizeHeadline(value: unknown): HeadlineRecord {
  const item = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
  return {
    title: asString(item.title),
    source: asString(item.source, "Unknown"),
    published_at: asString(item.published_at),
    url: asString(item.url),
    sentiment: asString(item.sentiment, "NEUTRAL"),
    deep_sentiment: asString(item.deep_sentiment, "measured_neutral"),
    positive_percent: asNumber(item.positive_percent),
    negative_percent: asNumber(item.negative_percent),
    neutral_percent: asNumber(item.neutral_percent),
    sentiment_intensity: asNumber(item.sentiment_intensity),
    dominant_emotion: asString(item.dominant_emotion, "neutral"),
    trust_percent: asNumber(item.trust_percent),
  };
}

function normalizeDeepSentimentSummary(value: unknown): DeepSentimentSummary {
  const item = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
  return {
    average_positive_signal: asNumber(item.average_positive_signal),
    average_negative_signal: asNumber(item.average_negative_signal),
    average_neutral_signal: asNumber(item.average_neutral_signal),
    average_intensity: asNumber(item.average_intensity),
    average_valence: asNumber(item.average_valence),
  };
}

function normalizeMetricRecord(value: unknown) {
  if (typeof value !== "object" || value === null) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, raw]) => [key, asNumber(raw)]).filter(([, raw]) => Number.isFinite(raw)),
  );
}

function normalizeSnapshot(value: unknown): LiveSnapshot {
  const item = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
  return {
    schema_version: asNumber(item.schema_version, 1),
    status: asString(item.status, "unknown"),
    generated_at: asString(item.generated_at),
    published_at: asString(item.published_at),
    last_updated: asString(item.last_updated, asString(item.generated_at)),
    cycle: asNumber(item.cycle, 1),
    query: asString(item.query, "geopolitics"),
    articles_count: asNumber(item.articles_count),
    article_count: asNumber(item.article_count),
    fetched_articles_count: asNumber(item.fetched_articles_count),
    new_articles_count: asNumber(item.new_articles_count),
    seen_articles_skipped: asNumber(item.seen_articles_skipped),
    message: asString(item.message),
    error: asString(item.error),
    sentiment_distribution: normalizeMetricRecord(item.sentiment_distribution),
    deep_sentiment_distribution: normalizeMetricRecord(item.deep_sentiment_distribution),
    deep_sentiment_summary: normalizeDeepSentimentSummary(item.deep_sentiment_summary),
    emotion_distribution: normalizeMetricRecord(item.emotion_distribution),
    average_trust_percent: asNumber(item.average_trust_percent),
    top_sources: normalizeMetricRecord(item.top_sources),
    headlines: Array.isArray(item.headlines) ? item.headlines.map(normalizeHeadline) : [],
  };
}

export async function loadSnapshotEnvelope(): Promise<LiveSnapshotEnvelope> {
  const blobPath = process.env.GNS_BLOB_SNAPSHOT_PATH || DEFAULT_PATH;

  try {
    const blob = await head(blobPath);
    const blobUrl = typeof blob.downloadUrl === "string" ? blob.downloadUrl : blob.url;
    const response = await fetch(blobUrl, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Blob fetch failed with HTTP ${response.status}`);
    }

    const snapshot = normalizeSnapshot(await response.json());
    return {
      source: "blob",
      blobPath,
      snapshot,
    };
  } catch (error) {
    return {
      source: "mock",
      blobPath,
      error: error instanceof Error ? error.message : "Blob snapshot unavailable",
      snapshot: mockSnapshot,
    };
  }
}
