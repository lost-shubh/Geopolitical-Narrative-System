# Free-Data Process

This project should move forward without depending on paid social-media APIs.

## Active Data Path

1. Stage 1 fetches live news.
   - Use NewsAPI when `NEWS_API_KEY` is configured.
   - If NewsAPI is missing, rate-limited, or returns no usable articles, use free no-key sources:
     GDELT DOC API first, then RSS search fallback.

2. Stage 2 builds public-reaction signals.
   - Preferred: analyze a user-provided export with `--comments-file`.
   - Fallback: derive reaction-like rows from the live article text itself.
   - Do not block the pipeline on Reddit, Twitter/X, or other paid platform APIs.

3. Stage 3 analyzes sentiment, emotion, polarization, and virality using the available reaction rows.

4. Stage 4 verifies claims with local article evidence, curated research-style evidence, and optional Google Fact Check when configured.

5. Stage 5 generates counter-narratives with the template generator by default. Optional LLM synthesis remains available when `OPENAI_API_KEY` is configured.

## Why This Direction

- It keeps the demo working even without paid API access.
- It improves real-time freshness through GDELT and RSS no-key coverage.
- It keeps social reaction analysis extensible through exported datasets instead of hard-coding one platform.
- It avoids waiting on platform approvals before improving the intelligence workflow.

## Next Engineering Priorities

1. Improve GDELT/RSS source diversity and query profiles.
2. Add a simple CSV/JSON import template for manually collected reactions.
3. Add evaluation reports comparing article-derived reaction signals against exported real comments.
4. Add dashboard labels that disclose whether reactions came from external exports or article-derived proxy rows.
