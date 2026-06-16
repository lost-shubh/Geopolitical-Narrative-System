# Geopolitical Narrative Intelligence System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Research](https://img.shields.io/badge/status-research-orange.svg)]()

> An NLP-powered intelligence system for detecting, analyzing, and countering false geopolitical narratives through evidence-based fact verification and automated counter-narrative synthesis.

**Live mode:** see [REALTIME.md](REALTIME.md) to run strict real-time news fetching and live dashboards.
If NewsAPI is unavailable, Stage 1 can continue with free no-key GDELT/RSS fallbacks.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Benchmark & Evaluation Metrics](#benchmark--evaluation-metrics)
- [Development Roadmap](#development-roadmap)
- [Ethical Framework](#ethical-framework)
- [Technical Details](#technical-details)
- [Contributing](#contributing)
- [License](#license)
- [Citation](#citation)

---

## 🎯 Overview

The **Geopolitical Narrative Intelligence System** is a research-grade pipeline that combines natural language processing, computational social science, and automated reasoning to:

1. **Monitor** geopolitical narratives across news and social media platforms
2. **Analyze** public emotional and ideological reactions to these narratives
3. **Verify** claims through fact-checking databases and academic research
4. **Synthesize** evidence-based counter-narratives with proper attribution

This system addresses the growing challenge of coordinated misinformation campaigns that influence public opinion on critical geopolitical issues.

---

## 🚨 Problem Statement

### The Challenge

Modern information warfare operates through:
- **Rapid narrative spread** across multiple platforms simultaneously
- **Emotional manipulation** designed to trigger fear, anger, or distrust
- **Coordinated amplification** by both human and automated accounts
- **Fragmented fact-checking** that arrives too late or lacks reach

### Our Approach

Rather than manual fact-checking after virality, this system provides:
- **Early detection** of emerging false narratives
- **Quantified analysis** of psychological impact on audiences
- **Automated evidence gathering** from trusted sources
- **Synthesized counter-narratives** that are both factual and persuasive

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     INPUT LAYER                              │
│  News APIs • Social Media • Comment Sections • Forums        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 1: CONTENT EXTRACTION                     │
│  • Named Entity Recognition (People, Places, Organizations)  │
│  • Topic Modeling & Clustering                               │
│  • Keyphrase Extraction                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           STAGE 2: REACTION COLLECTION                       │
│  • Social media post collection                              │
│  • Comment thread extraction                                 │
│  • Engagement metrics (likes, shares, replies)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           STAGE 3: REACTION ANALYSIS                         │
│  • Sentiment Analysis (positive/negative/neutral)            │
│  • Emotion Detection (anger, fear, trust, etc.)              │
│  • Polarization Metrics (ideological fragmentation)          │
│  • Virality Pattern Recognition                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            STAGE 4: FACT DISCOVERY                           │
│  • Claim Extraction (verifiable statements)                  │
│  • Fact-Check Database Search                                │
│  • Research Paper Retrieval                                  │
│  • Evidence Ranking by Credibility                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          STAGE 5: NARRATIVE SYNTHESIS                        │
│  • Evidence Compilation & Organization                       │
│  • Counter-Narrative Generation (LLM-based)                  │
│  • Tone Adjustment for Target Audience                       │
│  • Source Citation & Attribution                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                              │
│  Fact-Based Counter-Narrative • Evidence Report • Analytics  │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ How It Works

### Example Scenario

**1. Narrative Detected:**
> "Country X is secretly deploying biological weapons in Country Y."

**2. System Actions:**

**Stage 1 - Content Extraction:**
- Identifies entities: Country X, Country Y, "biological weapons"
- Clusters related articles across platforms
- Tracks narrative spread velocity

**Stage 2 - Reaction Collection:**
- Gathers 10,000+ social media comments
- Collects engagement metrics (shares, likes)
- Preserves temporal data for spread analysis

**Stage 3 - Reaction Analysis:**
```
Sentiment: 68% negative, 22% neutral, 10% positive
Emotions: Fear (0.71), Anger (0.58), Distrust (0.62)
Polarization: High (echo chamber formation detected)
Virality Score: 8.7/10 (rapid amplification)
```

**Stage 4 - Fact Discovery:**
- Extracts claim: "Country X possesses biological weapons"
- Searches fact-check databases → No evidence found
- Retrieves research papers on international weapons inspections
- Locates WHO/UN reports confirming no biological program exists
- Evidence quality score: 9.2/10 (high credibility sources)

**Stage 5 - Narrative Synthesis:**
```
COUNTER-NARRATIVE OUTPUT:

The claim that Country X is deploying biological weapons in Country Y 
lacks verifiable evidence. Here's what independent verification shows:

✓ The Organisation for the Prohibition of Chemical Weapons (OPCW) 
  conducted inspections in 2023 and found no biological weapons program 
  [Source: OPCW Report 2023, pg. 47]

✓ Multiple peer-reviewed studies examining Country X's military 
  capabilities find no indication of biological weapons development 
  [Journal of Strategic Studies, 2024]

✓ This narrative mirrors historical disinformation patterns used to 
  justify military intervention [Ref: Comparative Analysis of War 
  Propaganda, Smith et al., 2022]

While concerns about regional security are valid, claims require 
evidence-based verification through independent international bodies.
```

---

## 📁 Project Structure

```
geopolitical-narrative-system/
│
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git exclusions
├── LICENSE                            # MIT License
│
├── config/
│   ├── api_keys.example.yaml          # API configuration template
│   ├── model_config.yaml              # Model parameters
│   └── pipeline_config.yaml           # Pipeline settings
│
├── data/
│   ├── raw/
│   │   ├── news/                      # Raw news articles (JSON/CSV)
│   │   ├── social/                    # Social media posts
│   │   └── comments/                  # User reactions & comments
│   │
│   ├── processed/
│   │   ├── extracted_entities/        # NER outputs
│   │   ├── extracted_claims/          # Verifiable claims
│   │   ├── reaction_analysis/         # Sentiment/emotion data
│   │   └── evidence/                  # Gathered factual evidence
│   │
│   └── external/
│       ├── fact_checks/               # Fact-checking database exports
│       ├── research_papers/           # Academic sources (PDFs/metadata)
│       └── trusted_sources/           # Verified news corpora
│
├── src/
│   ├── __init__.py
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── news_ingestor.py           # News API/RSS/scraper
│   │   ├── social_ingestor.py         # External social/comment exports
│   │   └── comment_collector.py        # Comment thread extraction
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── clean_text.py              # Text normalization
│   │   ├── language_detect.py         # Multi-language support
│   │   └── entity_extraction.py       # NER (spaCy/Transformers)
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── claim_extraction.py        # Extract verifiable statements
│   │   ├── sentiment.py               # Sentiment analysis
│   │   ├── emotion.py                 # Emotion detection (27 emotions)
│   │   ├── polarization.py            # Ideological fragmentation metrics
│   │   └── engagement_metrics.py      # Virality & amplification analysis
│   │
│   ├── verification/
│   │   ├── __init__.py
│   │   ├── fact_finder.py             # Fact-check database search
│   │   ├── research_search.py         # Academic paper retrieval
│   │   ├── source_credibility.py      # Trust scoring algorithms
│   │   └── evidence_ranker.py         # Rank evidence by quality
│   │
│   ├── synthesis/
│   │   ├── __init__.py
│   │   ├── narrative_generator.py     # LLM-based counter-narrative
│   │   ├── evidence_compiler.py       # Organize supporting facts
│   │   └── citation_formatter.py      # Proper attribution
│   │
│   ├── models/
│   │   ├── embeddings/                # Pre-trained embeddings
│   │   ├── classifiers/               # Trained models
│   │   └── prompts/                   # LLM prompt templates
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                  # Centralized logging
│       ├── database.py                # Data persistence (SQLite/PostgreSQL)
│       └── api_clients.py             # External API wrappers
│
├── notebooks/
│   ├── 01_data_exploration.ipynb      # Initial data analysis
│   ├── 02_claim_extraction_dev.ipynb  # Claim detection experiments
│   ├── 03_fact_verification_dev.ipynb # Evidence retrieval testing
│   └── 04_narrative_synthesis_dev.ipynb # Counter-narrative generation
│
├── pipeline/
│   ├── main.py                        # Full pipeline orchestrator
│   ├── stage1_content_extraction.py   # News & entity extraction
│   ├── stage2_reaction_collection.py  # Social listening
│   ├── stage3_reaction_analysis.py    # Crowd psychology analysis
│   ├── stage4_fact_discovery.py       # Evidence gathering
│   └── stage5_narrative_synthesis.py  # Counter-narrative generation
│
└── tests/
    ├── test_ingestion.py              # Unit tests for data collection
    ├── test_preprocessing.py          # Text cleaning tests
    ├── test_analysis.py               # NLP pipeline tests
    └── test_verification.py           # Fact-checking tests
```

---

## 🔧 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/geopolitical-narrative-system.git
cd geopolitical-narrative-system
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Activate on macOS/Linux:
source venv/bin/activate

# Activate on Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download NLP Models

```bash
# spaCy language models
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg

# NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### Step 5: Configure API Keys

Copy `config/api_keys.example.yaml` to `config/api_keys.yaml`, then set `NEWS_API_KEY` in your environment or put the key in the local config file:

```yaml
news_api_env: NEWS_API_KEY
news_api_key: ""
require_news_api_key: true
google_factcheck_env: GOOGLE_FACTCHECK_API_KEY
google_factcheck_api_key: ""
enable_google_factcheck: true
```

**⚠️ Never commit `api_keys.yaml` to version control**

`GOOGLE_FACTCHECK_API_KEY` is optional. When it is set, Stage 4 adds Google Fact Check claim-review evidence to the local article and research evidence already used by the verifier.

---

## 🚀 Quick Start

### Run the Full Pipeline

```bash
python pipeline/main.py --topic "election interference" --days 7
```

### Run Individual Stages

```bash
# Stage 1: Extract news content
python pipeline/stage1_content_extraction.py --query "geopolitical conflict"

# Stage 2: Collect social reactions
python pipeline/stage2_reaction_collection.py --max-comments 25

# Stage 2 with an external social export
python pipeline/stage2_reaction_collection.py --comments-file data/raw/social/comments.json --max-comments 100

# Stage 2 can also derive reaction-like rows from article text when no export is available
python pipeline/stage2_reaction_collection.py --max-comments 100

# Stage 3: Analyze reactions
python pipeline/stage3_reaction_analysis.py

# Stage 4: Find factual evidence
python pipeline/stage4_fact_discovery.py --top-claims 10

# Stage 5: Generate counter-narrative
python pipeline/stage5_narrative_synthesis.py --tone analytical

# Stage 5 with optional LLM synthesis
python pipeline/stage5_narrative_synthesis.py --llm --llm-model gpt-4.1-mini --tone analytical
```

LLM synthesis is disabled by default and falls back to the template generator if `OPENAI_API_KEY` is not configured or the API request fails.

### Example Output

```json
{
  "narrative_id": "20250109_001",
  "original_claim": "Country X deploying biological weapons",
  "sentiment_analysis": {
    "negative": 0.68,
    "neutral": 0.22,
    "positive": 0.10
  },
  "emotions": {
    "fear": 0.71,
    "anger": 0.58,
    "distrust": 0.62
  },
  "polarization_score": 0.82,
  "evidence_summary": [
    {
      "source": "OPCW Report 2023",
      "credibility": 9.8,
      "finding": "No evidence of biological weapons program",
      "url": "https://opcw.org/..."
    }
  ],
  "counter_narrative": "Evidence-based refutation with citations...",
  "confidence": 0.91
}
```

---

## 🛣️ Development Roadmap

### ✅ Version 0.1 (Current) - Foundation
- [x] Project structure setup
- [x] Requirements definition
- [x] Architecture documentation
- [ ] Basic news ingestion
- [ ] Mock social media data collection
- [ ] Simple sentiment analysis

### 🔄 Version 0.2 - Core Analysis
- [ ] Free/open data integrations (GDELT, NewsAPI fallback, exported public comments)
- [ ] Multi-source content aggregation
- [ ] Advanced sentiment & emotion detection
- [ ] Polarization metrics implementation
- [ ] Data visualization dashboard

### 📅 Version 0.3 - Intelligence Layer
- [ ] Claim extraction algorithms
- [ ] Fact-check database integration
- [ ] Research paper search (Semantic Scholar, PubMed)
- [ ] Source credibility scoring
- [ ] Evidence ranking system

### 🎯 Version 0.4 - Synthesis
- [ ] LLM integration for narrative generation
- [ ] Prompt engineering for counter-narratives
- [ ] Multi-tone output (academic, social, policy)
- [ ] Automated citation formatting
- [ ] Quality assurance checks

### 🚀 Version 1.0 - Production
- [ ] Real-time monitoring
- [ ] Scalable pipeline (Airflow/Nextflow)
- [ ] Web API + Dashboard
- [ ] Multi-language support
- [ ] Performance optimization
- [ ] Comprehensive testing suite

---

## ⚖️ Ethical Framework

### Core Principles

This system is built on strict ethical guidelines:

1. **Truth Over Persuasion**
   - All counter-narratives must be grounded in verifiable evidence
   - Uncertainty is acknowledged explicitly
   - No speculation presented as fact

2. **Transparency**
   - All sources are cited with full attribution
   - Methodology is openly documented
   - Limitations are clearly stated

3. **Privacy Protection**
   - User data is anonymized
   - No individual targeting
   - Aggregate analysis only

4. **Non-Manipulation**
   - No emotional exploitation
   - No creation of counter-propaganda
   - Respects audience agency

5. **Accountability**
   - Auditable decision processes
   - Version-controlled outputs
   - Error correction mechanisms

### Red Lines (Never Cross)

❌ **DO NOT:**
- Generate false counter-narratives
- Target or doxx individuals
- Manipulate emotional reactions for political gain
- Create content that could incite violence
- Bypass informed consent requirements
- Misrepresent uncertainty as certainty

✅ **ALWAYS:**
- Prioritize accuracy
- Cite sources transparently
- Acknowledge limitations
- Respect human dignity
- Follow research ethics protocols

---

## 🔬 Technical Details

### NLP & ML Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Named Entity Recognition** | spaCy, Flair | Extract people, places, organizations |
| **Topic Modeling** | BERTopic, LDA | Cluster related narratives |
| **Sentiment Analysis** | transformers (DistilBERT) | Detect positive/negative/neutral tone |
| **Emotion Detection** | j-hartmann/emotion-distilroberta | Identify specific emotions (27 types) |
| **Claim Extraction** | Dependency parsing, GPT-4 | Isolate verifiable statements |
| **Semantic Search** | sentence-transformers | Find related evidence |
| **Text Generation** | GPT-4, Claude | Generate counter-narratives |
| **Document Retrieval** | Elasticsearch, FAISS | Search fact databases |

### Data Sources

**News:**
- NewsAPI
- RSS feeds (Reuters, AP, BBC)
- Web scraping (ethical, rate-limited)

**Social Media:**
- Twitter/X API v2
- Optional exported social/comment datasets
- YouTube Data API

**Fact-Checking:**
- FactCheck.org
- Snopes API
- PolitiFact
- International Fact-Checking Network (IFCN)

**Research:**
- Semantic Scholar API
- PubMed Central
- arXiv
- Google Scholar (limited scraping)

### Performance Considerations

- **Scalability:** Designed for 10,000+ articles/day processing
- **Latency:** Sub-5-minute analysis for breaking narratives
- **Storage:** PostgreSQL for structured data, object storage for raw content
- **Computing:** Optimized for CPU inference, GPU optional for embeddings

---

## 📊 Research Applications

This system enables research into:

1. **Information Warfare Dynamics**
   - Cross-platform narrative coordination
   - State-sponsored vs organic spread patterns
   - Temporal evolution of false narratives

2. **Computational Social Science**
   - Crowd psychology during crises
   - Emotional contagion patterns
   - Polarization formation mechanisms

3. **Intervention Effectiveness**
   - Impact of fact-based corrections
   - Optimal counter-narrative strategies
   - Audience receptivity factors

4. **Media Ecosystem Analysis**
   - Source credibility networks
   - Misinformation amplification pathways
   - Echo chamber formation

---

## 🤝 Contributing

We welcome contributions from:
- NLP researchers
- Data scientists
- Fact-checkers and journalists
- Social scientists
- Policy analysts

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Guidelines

- Follow PEP 8 style guide
- Add unit tests for new features
- Update documentation
- Ensure ethical compliance
- Cite relevant research

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Important Notes on Use

This system is intended for:
- Academic research
- Journalistic fact-checking
- Policy analysis
- Educational purposes

**Not intended for:**
- Political campaigning
- Commercial manipulation
- Surveillance
- Censorship

Users are responsible for ensuring ethical and legal compliance in their jurisdiction.

---

## 📚 Citation

If you use this system in your research, please cite:

```bibtex
@software{geopolitical_narrative_system,
  title = {Geopolitical Narrative Intelligence System},
  author = Shubh Gupta,
  year = {2025},
  url = {https://github.com/lost-shubh/geopolitical-narrative-system},
  note = {An NLP-powered system for detecting and countering false geopolitical narratives}
}
```

---

## 📞 Contact

- **Project Lead:** Shubh Gupta - [shubh056888@gmail.com]
- **GitHub:** [lost-shubh](https://github.com/lost-shubh)
- **Issues:** [GitHub Issues](https://github.com/lost-shubh/geopolitical-narrative-system/issues)

---

## 🙏 Acknowledgments

This project builds on research from:
- Computational propaganda studies
- Argumentation mining
- Automated fact-checking
- Natural language inference
- Cognitive security

Special thanks to the open-source NLP community and ethical AI researchers whose work makes projects like this possible.

---

## ⚠️ Disclaimer

This system is a research tool. While we strive for accuracy, automated fact-checking and narrative analysis have inherent limitations. Human oversight and verification remain essential. Users should:

- Verify findings independently
- Consider multiple perspectives
- Consult domain experts
- Recognize system limitations
- Use responsibly and ethically

---

**Built with ❤️ for truth, transparency, and informed public discourse.**
---

## Benchmark & Evaluation Metrics

The project uses pretrained NLP backbones for sentiment, emotion, and NER. The table below separates:

- model benchmark metrics for the exact pretrained models configured in this repo
- operational pipeline metrics measured from local GNS runs and reports

### Model-Level Metrics

| Component | Model used in GNS | Accuracy | F1-Score | ROC-AUC | Precision | Recall | Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Sentiment analysis | `distilbert-base-uncased-finetuned-sst-2-english` | 91.1% | 91.4% | 97.2% | 89.8% | 93.0% | [Hugging Face model card](https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english) |
| Emotion analysis | `j-hartmann/emotion-english-distilroberta-base` | 66.0% | - | - | - | - | [Hugging Face model card](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base) |
| Named entity recognition | `en_core_web_sm` | - | 84.56% | - | 84.55% | 84.57% | [spaCy model card](https://huggingface.co/spacy/en_core_web_sm) |

### Pipeline-Level Runtime Metrics

These are the current GNS runtime benchmarks documented in the repo:

| Pipeline step | Measured throughput |
| --- | ---: |
| News ingestion | ~2-5 seconds per 10 articles |
| Sentiment analysis | ~0.5 seconds per article |
| Emotion analysis | ~1 second per article |
| Claim extraction | ~2-3 seconds per article |
| Full end-to-end pipeline | ~3-5 minutes for 10 articles |

Source: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

### Latest End-to-End Pipeline Run

The latest recorded local pipeline run produced the following system-level outputs:

| Metric | Value | Source |
| --- | ---: | --- |
| Articles analyzed | 9 | [pipeline_run_summary.json](data/processed/pipeline_results/pipeline_run_summary.json) |
| Comments analyzed | 9 | [FINAL_REPORT.txt](data/processed/pipeline_results/FINAL_REPORT.txt) |
| Verified claims | 10 | [FINAL_REPORT.txt](data/processed/pipeline_results/FINAL_REPORT.txt) |
| Generated counter-narratives | 10 | [FINAL_REPORT.txt](data/processed/pipeline_results/FINAL_REPORT.txt) |
| Average evidence credibility | 0.87 | [FINAL_REPORT.txt](data/processed/pipeline_results/FINAL_REPORT.txt) |
| Negative coverage in latest run | 77.78% | [FINAL_REPORT.txt](data/processed/pipeline_results/FINAL_REPORT.txt) |
| Polarization level | 1.0 (high) | [FINAL_REPORT.txt](data/processed/pipeline_results/FINAL_REPORT.txt) |

### Reporting Note

- `F1-Score`, `Accuracy`, and `ROC-AUC` are now explicitly visible in this README.
- The sentiment metrics above come from the exact pretrained sentiment backbone configured in [`src/analysis/sentiment.py`](src/analysis/sentiment.py).
- The emotion and NER metrics come from the exact pretrained backbones configured in [`src/analysis/emotion.py`](src/analysis/emotion.py) and [`src/preprocessing/entity_extraction.py`](src/preprocessing/entity_extraction.py).
- The current repository does not yet contain a labeled end-to-end GNS benchmark dataset for reporting a single unified system-wide ROC-AUC or F1, so those values are reported at the model-component level rather than as a fabricated overall score.
