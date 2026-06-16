\# 🚀 Quick Start Guide



\## Run Everything in One Command



```powershell

python run\_pipeline.py

```



That's it! This runs the complete end-to-end analysis.



---



\## What Happens



The pipeline automatically:



1\. \*\*Fetches geopolitical news\*\* (or uses existing data)

2\. \*\*Collects social reaction rows\*\* from an external JSON export, or derives a news-based reaction proxy when no export is provided

3\. \*\*Analyzes news sentiment \& emotions\*\*

4\. \*\*Analyzes public reaction sentiment \& emotions\*\*

5\. \*\*Compares media vs. public perception\*\*

6\. \*\*Generates comprehensive report\*\*



---



\## Output Files



After running, check these files:



\### \*\*📊 Main Report\*\*

```

data/processed/pipeline\_results/FINAL\_REPORT.txt

```

Human-readable comprehensive analysis



\### \*\*📁 Detailed Data\*\*

```

data/processed/pipeline\_results/news\_analysis.json

data/processed/pipeline\_results/social\_analysis.json

```

Full analysis with all data



---



\## Expected Runtime



\- \*\*First run:\*\* 5-10 minutes (downloads AI models)

\- \*\*Subsequent runs:\*\* 2-3 minutes



---



\## Step-by-Step (Alternative)



If you want to run stages individually:



\### \*\*Stage 1: Fetch News\*\*

```powershell

python test\_news\_ingestion.py

```



\### \*\*Stage 2: Collect Reaction Data\*\*

```powershell

python pipeline/stage2\_reaction_collection.py --max-comments 25

# Optional: use a real social export
python pipeline/stage2\_reaction_collection.py --comments-file data/raw/social/comments.json --max-comments 100

```



\### \*\*Stage 3: Analyze Everything\*\*

```powershell

python test\_analysis.py

python analyze\_social\_comments.py

```



---



\## Sample Output



```

============================================================

&nbsp; GEOPOLITICAL NARRATIVE INTELLIGENCE SYSTEM

&nbsp; Complete Analysis Pipeline

============================================================



Started: 2026-01-16 14:30:00



======================================================================

&nbsp; STAGE 1: NEWS INGESTION

======================================================================



🔄 Initializing news ingestor...

📰 Fetching geopolitical news (last 3 days)...

✓ Fetched 15 articles

✓ From 8 unique sources



======================================================================

&nbsp; STAGE 2: SOCIAL MEDIA DATA

======================================================================



✓ Using external social export or news-derived reaction proxy

✓ Loaded 25 reaction rows



======================================================================

&nbsp; STAGE 3A: NEWS SENTIMENT \& EMOTION ANALYSIS

======================================================================



📂 Loading articles from: data/raw/news/pipeline\_news.json

✓ Loaded 15 articles



🔄 Running sentiment analysis...

✓ Sentiment: 3 positive, 10 negative, 2 neutral



🔄 Running emotion analysis...

✓ Dominant emotion: fear



======================================================================

&nbsp; STAGE 3B: SOCIAL MEDIA SENTIMENT \& EMOTION ANALYSIS

======================================================================



📂 Loading reaction rows from: data/processed/stage2_reaction_collection/relevant_comments.json

✓ Loaded 25 reaction rows



🔄 Analyzing sentiment...

🔄 Analyzing emotions...



✓ Sentiment: 45 positive (19.5%), 142 negative (61.5%)

✓ Dominant emotion: fear (28.6%)



======================================================================

&nbsp; GENERATING FINAL REPORT

======================================================================



✓ Final report saved to: data/processed/pipeline\_results/FINAL\_REPORT.txt



======================================================================

&nbsp; ✅ PIPELINE COMPLETE

======================================================================



📁 Output Files:

&nbsp; • News analysis:   data/processed/pipeline\_results/news\_analysis.json

&nbsp; • Social analysis: data/processed/pipeline\_results/social\_analysis.json

&nbsp; • Final report:    data/processed/pipeline\_results/FINAL\_REPORT.txt



📊 Quick Summary:

&nbsp; • Analyzed 15 news articles

&nbsp; • Analyzed 231 social media comments

&nbsp; • News negativity:   66.7%

&nbsp; • Public negativity: 61.5%



📄 Read the full report: data/processed/pipeline\_results/FINAL\_REPORT.txt



🎉 Analysis complete! Check the output files above.

```



---



\## Sample Final Report



```

======================================================================

&nbsp; GEOPOLITICAL NARRATIVE INTELLIGENCE SYSTEM

&nbsp; COMPREHENSIVE ANALYSIS REPORT

======================================================================



Generated: 2026-01-16 14:32:15



======================================================================

SECTION 1: NEWS MEDIA ANALYSIS

======================================================================



Total Articles Analyzed: 15



Sentiment Distribution:

&nbsp; Positive: 3 (20.0%)

&nbsp; Negative: 10 (66.7%)

&nbsp; Neutral:  2 (13.3%)



Dominant Emotion in Coverage: FEAR



Emotion Distribution:

&nbsp; Fear        :  45.2%

&nbsp; Anger       :  22.1%

&nbsp; Sadness     :  18.3%

&nbsp; Neutral     :  10.5%

&nbsp; Surprise    :   3.9%



======================================================================

SECTION 2: PUBLIC REACTION ANALYSIS

======================================================================



Total Comments Analyzed: 231



Public Sentiment:

&nbsp; POSITIVE  : 45 (19.5%)

&nbsp; NEGATIVE  : 142 (61.5%)

&nbsp; NEUTRAL   : 44 (19.0%)



Public Emotions:

&nbsp; Fear        : 66 (28.6%)

&nbsp; Anger       : 58 (25.1%)

&nbsp; Sadness     : 42 (18.2%)

&nbsp; Neutral     : 39 (16.9%)

&nbsp; Disgust     : 26 (11.3%)



======================================================================

SECTION 3: MEDIA vs. PUBLIC COMPARISON

======================================================================



Sentiment Analysis:

&nbsp; News negativity:   66.7%

&nbsp; Public negativity: 61.5%

&nbsp; Gap: 5.2% (public LESS negative)



======================================================================

SECTION 4: KEY INSIGHTS

======================================================================



• News coverage is predominantly NEGATIVE - potential crisis framing

• Public sentiment is highly NEGATIVE - strong emotional reactions

• News coverage evokes FEAR - potentially alarming framing

• Public reactions show high FEAR - emotional escalation



======================================================================

SECTION 5: RECOMMENDATIONS

======================================================================



1\. High public negativity detected - fact-based corrections needed

3\. Fear-driven reactions - provide context and reassurance



======================================================================

END OF REPORT

======================================================================

```



---



\## Troubleshooting



\### "NEWS\_API\_KEY not found"

\*\*Solution:\*\* The pipeline will use existing data or skip news fetching. To enable:

1\. Get free API key from https://newsapi.org/register

2\. Add to `.env` file: `NEWS\_API\_KEY=your\_key\_here`



\### "Module not found" errors

\*\*Solution:\*\* Install requirements:

```powershell

pip install -r requirements.txt

python -m spacy download en\_core\_web\_sm

```



\### Pipeline is slow

\*\*First run takes longer\*\* - AI models are downloading (1-2GB). Subsequent runs are much faster.



---



\## Next Steps



After running the pipeline:



1\. \*\*Read the report:\*\* Open `FINAL\_REPORT.txt`

2\. \*\*Explore the data:\*\* Check JSON files for detailed analysis

3\. \*\*Run with real data:\*\* Use NewsAPI/GDELT for live news and add exported public-comment datasets when available

4\. \*\*Build Stage 4:\*\* Extract and verify claims from articles



---



\## Commands Cheat Sheet



```powershell

\# Full pipeline (recommended)

python run\_pipeline.py



\# Individual stages

python test\_news\_ingestion.py          # Stage 1

python create\_mock\_data.py             # Stage 2

python test\_analysis.py                # Stage 3a

python analyze\_social\_comments.py      # Stage 3b



\# View results

notepad data\\processed\\pipeline\_results\\FINAL\_REPORT.txt

```



---



\*\*Questions?\*\* Check the main README.md or create an issue on GitHub.

