export type MetricRecord = Record<string, number>;

export interface HeadlineRecord {
  title: string;
  source: string;
  published_at: string;
  url: string;
  sentiment: string;
  deep_sentiment: string;
  positive_percent: number;
  negative_percent: number;
  neutral_percent: number;
  sentiment_intensity: number;
  dominant_emotion: string;
  trust_percent: number;
}

export interface DeepSentimentSummary {
  average_positive_signal: number;
  average_negative_signal: number;
  average_neutral_signal: number;
  average_intensity: number;
  average_valence: number;
}

export interface LiveSnapshot {
  schema_version: number;
  status: string;
  generated_at: string;
  published_at?: string;
  last_updated: string;
  cycle: number;
  query: string;
  articles_count: number;
  article_count: number;
  fetched_articles_count: number;
  new_articles_count: number;
  seen_articles_skipped: number;
  message?: string;
  error?: string;
  sentiment_distribution: MetricRecord;
  deep_sentiment_distribution: MetricRecord;
  deep_sentiment_summary: DeepSentimentSummary;
  emotion_distribution: MetricRecord;
  average_trust_percent: number;
  top_sources: MetricRecord;
  headlines: HeadlineRecord[];
}

export interface LiveSnapshotEnvelope {
  source: "blob" | "error";
  blobPath: string;
  error?: string;
  snapshot: LiveSnapshot;
}
