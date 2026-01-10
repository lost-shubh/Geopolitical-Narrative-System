# Setup Instructions

Complete guide to setting up the Geopolitical Narrative Intelligence System development environment.

---

## 📋 Prerequisites

### System Requirements
- **Python:** 3.8, 3.9, 3.10, or 3.11 (3.11 recommended)
- **RAM:** Minimum 8GB (16GB recommended for full pipeline)
- **Storage:** 5GB free space (for models and data)
- **OS:** Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)

### Required Software
- Git
- pip (comes with Python)
- Virtual environment tool (venv or conda)

---

## 🚀 Quick Start (Minimal Setup)

For initial development and testing:

```bash
# 1. Clone repository
git clone https://github.com/yourusername/geopolitical-narrative-system.git
cd geopolitical-narrative-system

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install minimal dependencies
pip install -r requirements-minimal.txt

# 5. Download NLP models
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"

# 6. Test installation
python -c "import spacy, transformers, pandas; print('✓ Setup successful')"
```

---

## 🔧 Full Installation

For production-ready development:

### Step 1: System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    build-essential
```

#### macOS
```bash
brew install postgresql libxml2 libxslt
```

#### Windows
No additional system dependencies required. Use WSL2 for better compatibility.

---

### Step 2: Python Environment

#### Option A: venv (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

#### Option B: conda
```bash
conda create -n geopolitical-narrative python=3.11
conda activate geopolitical-narrative
```

---

### Step 3: Install PyTorch

**Choose based on your hardware:**

#### CPU Only
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### CUDA 11.8 (NVIDIA GPU)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### CUDA 12.1 (Latest NVIDIA GPU)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### macOS (Metal/MPS)
```bash
pip install torch torchvision torchaudio
```

---

### Step 4: Install Main Dependencies

```bash
pip install -r requirements.txt
```

**If you encounter errors:**
```bash
# Install problematic packages individually
pip install numpy pandas scipy
pip install transformers sentence-transformers
pip install spacy nltk
pip install beautifulsoup4 lxml
pip install scikit-learn
```

---

### Step 5: Download NLP Models

#### spaCy Models
```bash
# Small model (fast, less accurate)
python -m spacy download en_core_web_sm

# Large model (slower, more accurate)
python -m spacy download en_core_web_lg

# Multilingual (if needed)
python -m spacy download xx_ent_wiki_sm
```

#### NLTK Data
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon'); nltk.download('averaged_perceptron_tagger')"
```

#### Transformers Models (Auto-downloaded on first use)
These will download automatically when first used:
- `distilbert-base-uncased-finetuned-sst-2-english` (sentiment)
- `j-hartmann/emotion-english-distilroberta-base` (emotion)
- `sentence-transformers/all-MiniLM-L6-v2` (embeddings)

---

### Step 6: Environment Configuration

Create `.env` file in project root:

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**`.env` contents:**
```env
# News APIs
NEWS_API_KEY=your_newsapi_key_here

# Social Media APIs
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=geopolitical-narrative-bot/0.1

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/geopolitical_narratives

# Optional: LLM APIs (for narrative generation)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Semantic Scholar
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key
```

---

### Step 7: Create Configuration Files

Create `config/api_keys.yaml`:

```yaml
news:
  newsapi:
    key: ${NEWS_API_KEY}
  
social_media:
  twitter:
    bearer_token: ${TWITTER_BEARER_TOKEN}
  reddit:
    client_id: ${REDDIT_CLIENT_ID}
    client_secret: ${REDDIT_CLIENT_SECRET}
    user_agent: ${REDDIT_USER_AGENT}
  youtube:
    api_key: ${YOUTUBE_API_KEY}

llm:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo-preview
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-opus-20240229

research:
  semantic_scholar:
    api_key: ${SEMANTIC_SCHOLAR_API_KEY}
```

---

### Step 8: Initialize Database (Optional)

If using PostgreSQL:

```bash
# Install PostgreSQL (if not already installed)
# Ubuntu: sudo apt-get install postgresql
# macOS: brew install postgresql

# Create database
createdb geopolitical_narratives

# Initialize schema (after implementing database.py)
python -c "from src.utils.database import init_db; init_db()"
```

---

### Step 9: Verify Installation

Run verification script:

```bash
python scripts/verify_setup.py
```

Or manually:

```python
# test_imports.py
print("Testing imports...")

# Core
import numpy as np
import pandas as pd
print("✓ Core libraries")

# NLP
import spacy
import nltk
from transformers import pipeline
print("✓ NLP libraries")

# APIs
import tweepy
import praw
print("✓ API clients")

# Load models
nlp = spacy.load("en_core_web_sm")
sentiment = pipeline("sentiment-analysis")
print("✓ Models loaded")

print("\n✅ All dependencies installed successfully!")
```

---

## 🔑 Getting API Keys

### NewsAPI
1. Visit https://newsapi.org/register
2. Free tier: 100 requests/day
3. Copy API key

### Twitter/X API
1. Apply for developer account: https://developer.twitter.com
2. Create project and app
3. Generate Bearer Token
4. Note: Free tier restrictions apply

### Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Create app (script type)
3. Copy client ID and secret
4. User agent: `geopolitical-narrative-bot/0.1`

### YouTube Data API
1. Visit Google Cloud Console: https://console.cloud.google.com
2. Create project
3. Enable YouTube Data API v3
4. Create credentials (API key)
5. Quota: 10,000 units/day (free)

### Semantic Scholar
1. Visit https://www.semanticscholar.org/product/api
2. Request API key (optional, higher rate limits)
3. Free tier: 100 requests/5 minutes

### OpenAI (Optional)
1. Visit https://platform.openai.com
2. Add payment method
3. Create API key
4. Monitor usage

### Anthropic (Optional)
1. Visit https://console.anthropic.com
2. Request access
3. Generate API key
4. Pay-as-you-go pricing

---

## 🧪 Testing Your Setup

### Test Individual Components

```bash
# Test news ingestion
python -m src.ingestion.news_ingestor --test

# Test sentiment analysis
python -m src.analysis.sentiment --test

# Test full pipeline
python pipeline/main.py --dry-run
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. PyTorch Installation Fails
```bash
# Try installing separately
pip install torch --no-cache-dir
```

#### 2. spaCy Model Not Found
```bash
python -m spacy download en_core_web_sm --force
python -m spacy validate
```

#### 3. SSL Certificate Errors
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

#### 4. Memory Errors During Installation
```bash
# Install packages one at a time
pip install numpy pandas
pip install transformers
# Continue...
```

#### 5. Permission Errors (Linux/macOS)
```bash
# Don't use sudo with pip!
# Use virtual environment instead
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 6. Transformers Model Download Fails
```bash
# Set cache directory
export TRANSFORMERS_CACHE=/path/to/large/disk
# or in Python:
import os
os.environ['TRANSFORMERS_CACHE'] = '/path/to/cache'
```

---

## 📦 Optional: Docker Setup

For consistent environments across machines:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLP models
RUN python -m spacy download en_core_web_sm && \
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

COPY . .

CMD ["python", "pipeline/main.py"]
```

Build and run:
```bash
docker build -t geopolitical-narrative .
docker run -v $(pwd)/data:/app/data geopolitical-narrative
```

---

## 🔄 Updating Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade transformers

# Regenerate lock file
pip freeze > requirements-lock.txt
```

---

## 🧹 Clean Installation

If something goes wrong, start fresh:

```bash
# Deactivate environment
deactivate

# Remove environment
rm -rf venv/

# Remove cache
rm -rf __pycache__ .pytest_cache
pip cache purge

# Start over
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 💾 Storage Requirements

Approximate disk space needed:

| Component | Size |
|-----------|------|
| Base Python packages | ~2 GB |
| spaCy models (small) | ~50 MB |
| spaCy models (large) | ~800 MB |
| Transformers models | ~1-2 GB |
| NLTK data | ~100 MB |
| Data cache | ~500 MB |
| **Total** | **~4-6 GB** |

---

## 🚀 Next Steps

After successful setup:

1. ✅ Verify all imports work
2. ✅ Test API connections
3. ✅ Run minimal pipeline test
4. 📖 Read [CONTRIBUTING.md](CONTRIBUTING.md)
5. 🔨 Start developing!

---

## 📞 Getting Help

If you encounter issues:

1. Check [GitHub Issues](https://github.com/yourusername/geopolitical-narrative-system/issues)
2. Review error messages carefully
3. Search Stack Overflow
4. Create detailed issue report with:
   - OS and Python version
   - Full error traceback
   - Steps to reproduce

---

**Happy coding! 🎉**