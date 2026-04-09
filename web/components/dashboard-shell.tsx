"use client";

import { startTransition, useEffect, useState } from "react";
import { StatusBadge } from "@/components/status-badge";
import type { LiveSnapshotEnvelope } from "@/src/lib/types";

function formatTime(value?: string) {
  if (!value) {
    return "Unknown";
  }

  try {
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function numberEntries(record: Record<string, number>) {
  return Object.entries(record).sort((left, right) => right[1] - left[1]);
}

function percentWidth(value: number) {
  return `${Math.max(6, Math.min(100, value))}%`;
}

export function DashboardShell({ initialEnvelope }: { initialEnvelope: LiveSnapshotEnvelope }) {
  const [envelope, setEnvelope] = useState(initialEnvelope);
  const [intervalSeconds, setIntervalSeconds] = useState(60);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setRefreshing(true);
      startTransition(async () => {
        try {
          const response = await fetch("/api/snapshot", { cache: "no-store" });
          if (!response.ok) {
            throw new Error(`Snapshot refresh failed with ${response.status}`);
          }
          const nextEnvelope = (await response.json()) as LiveSnapshotEnvelope;
          setEnvelope(nextEnvelope);
        } catch (error) {
          console.error(error);
        } finally {
          setRefreshing(false);
        }
      });
    }, intervalSeconds * 1000);

    return () => window.clearInterval(timer);
  }, [intervalSeconds]);

  const snapshot = envelope.snapshot;
  const sentimentRows = numberEntries(snapshot.sentiment_distribution);
  const deepSentimentRows = numberEntries(snapshot.deep_sentiment_distribution);
  const emotionRows = numberEntries(snapshot.emotion_distribution);
  const sourceRows = numberEntries(snapshot.top_sources);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      const response = await fetch("/api/snapshot", { cache: "no-store" });
      const nextEnvelope = (await response.json()) as LiveSnapshotEnvelope;
      setEnvelope(nextEnvelope);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <main className="dashboard-shell">
      <section className="hero">
        <article className="hero-card">
          <span className="eyebrow">Global narrative monitor</span>
          <h1>Geopolitical signals, published live.</h1>
          <p>
            This dashboard mirrors the live terminal monitor and exposes the latest headline mix, trust profile,
            emotional tone, and sentiment pressure from the current NewsAPI refresh window.
          </p>
          <div className="hero-meta">
            <span className="meta-pill">Query: {snapshot.query}</span>
            <span className="meta-pill">Updated: {formatTime(snapshot.generated_at)}</span>
            <span className="meta-pill">Source: {envelope.source}</span>
          </div>
          {envelope.error ? <p className="error-copy">{envelope.error}</p> : null}
        </article>

        <div className="hero-side">
          <aside className="panel">
            <div className="status-row">
              <div>
                <h2>System status</h2>
                <div className="subtle">Storage path: {envelope.blobPath}</div>
              </div>
              <StatusBadge status={snapshot.status} />
            </div>
            <p className="footer-note">
              {snapshot.message || "Latest successful refresh is available to every public visitor through Vercel."}
            </p>
          </aside>

          <aside className="panel">
            <h2>Refresh controls</h2>
            <div className="toolbar-actions">
              <button className="button" onClick={handleRefresh} type="button">
                {refreshing ? "Refreshing..." : "Refresh now"}
              </button>
              <select
                aria-label="Refresh interval"
                className="select"
                onChange={(event) => setIntervalSeconds(Number(event.target.value))}
                value={intervalSeconds}
              >
                <option value={30}>30 sec</option>
                <option value={60}>60 sec</option>
                <option value={120}>120 sec</option>
                <option value={300}>300 sec</option>
              </select>
            </div>
            <p className="footer-note">The page polls the server route instead of exposing Blob credentials to the browser.</p>
          </aside>
        </div>
      </section>

      <section className="section">
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-label">Headlines shown</div>
            <div className="metric-value">{snapshot.new_articles_count}</div>
            <div className="metric-note">Cards rendered this refresh</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Fetched total</div>
            <div className="metric-value">{snapshot.fetched_articles_count}</div>
            <div className="metric-note">Articles returned by NewsAPI</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Trust average</div>
            <div className="metric-value">{snapshot.average_trust_percent.toFixed(1)}%</div>
            <div className="metric-note">Source credibility score</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Intensity</div>
            <div className="metric-value">{snapshot.deep_sentiment_summary.average_intensity.toFixed(2)}</div>
            <div className="metric-note">Average sentiment force</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Valence</div>
            <div className="metric-value">{snapshot.deep_sentiment_summary.average_valence.toFixed(2)}</div>
            <div className="metric-note">Positive vs negative balance</div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="distribution-grid">
          <div className="distribution-card">
            <h3 className="section-title">Sentiment distribution</h3>
            <div className="distribution-list">
              {sentimentRows.map(([label, value]) => (
                <div className="distribution-row" key={label}>
                  <div className="distribution-meta">
                    <span>{label}</span>
                    <span>{value}</span>
                  </div>
                  <div className="distribution-track">
                    <div className="distribution-bar" style={{ width: percentWidth(value) }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="distribution-card">
            <h3 className="section-title">Deep sentiment</h3>
            <div className="distribution-list">
              {deepSentimentRows.map(([label, value]) => (
                <div className="distribution-row" key={label}>
                  <div className="distribution-meta">
                    <span>{label}</span>
                    <span>{value}</span>
                  </div>
                  <div className="distribution-track">
                    <div className="distribution-bar" style={{ width: percentWidth(value) }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="distribution-card">
            <h3 className="section-title">Dominant emotions</h3>
            <div className="distribution-list">
              {emotionRows.map(([label, value]) => (
                <div className="distribution-row" key={label}>
                  <div className="distribution-meta">
                    <span>{label}</span>
                    <span>{value}</span>
                  </div>
                  <div className="distribution-track">
                    <div className="distribution-bar" style={{ width: percentWidth(value) }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="panel">
          <div className="toolbar">
            <div>
              <h2>Latest headlines</h2>
              <div className="subtle">Matches the live terminal table, rebuilt for the web.</div>
            </div>
            <div className="subtle">
              Top sources: {sourceRows.map(([label, count]) => `${label} (${count})`).join(", ") || "N/A"}
            </div>
          </div>

          <div className="headlines-grid">
            {snapshot.headlines.length > 0 ? (
              snapshot.headlines.map((headline) => (
                <article className="headline-card" key={`${headline.url}-${headline.title}`}>
                  <div className="headline-topline">
                    <span className="headline-source">{headline.source}</span>
                    <StatusBadge status={headline.deep_sentiment || headline.sentiment || "unknown"} />
                  </div>
                  <div className="headline-title">{headline.title}</div>
                  <div className="headline-tags">
                    <span className="tag">Trust {headline.trust_percent.toFixed(1)}%</span>
                    <span className="tag">Emotion {headline.dominant_emotion}</span>
                    <span className="tag">+{headline.positive_percent}%</span>
                    <span className="tag">-{headline.negative_percent}%</span>
                    <span className="tag">={headline.neutral_percent}%</span>
                    <span className="tag">Intensity {headline.sentiment_intensity.toFixed(2)}</span>
                  </div>
                  <div className="headline-meta subtle">Published {formatTime(headline.published_at)}</div>
                  <a className="headline-link" href={headline.url} rel="noreferrer" target="_blank">
                    Read source
                  </a>
                </article>
              ))
            ) : (
              <div className="headline-card">
                <div className="headline-title">No live headlines are available right now.</div>
                <p className="subtle">
                  The dashboard remains reachable, but the latest refresh either returned zero qualifying articles or
                  degraded due to an upstream NewsAPI issue.
                </p>
              </div>
            )}
          </div>

          <p className="footer-note">
            Last updated {formatTime(snapshot.generated_at)}. Current storage source: {envelope.source}.
          </p>
        </div>
      </section>
    </main>
  );
}
