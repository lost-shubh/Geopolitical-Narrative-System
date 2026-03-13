"""
Claim Extraction Module - Stage 4
Extracts verifiable factual claims from news articles using NLP.
"""

import sys
from pathlib import Path
import json
import spacy
from typing import List, Dict
import re


class ClaimExtractor:
    """Extract factual claims from text using dependency parsing."""
    
    # Verbs that typically introduce factual claims
    CLAIM_VERBS = {
        'say', 'said', 'claim', 'claims', 'claimed', 'state', 'states', 'stated',
        'report', 'reports', 'reported', 'announce', 'announced', 'confirm', 'confirmed',
        'reveal', 'revealed', 'declare', 'declared', 'assert', 'asserted',
        'allege', 'alleged', 'accuse', 'accused', 'deny', 'denied'
    }
    
    # Patterns that indicate factual statements
    FACTUAL_PATTERNS = [
        r'\b\d+\s*(people|civilians|soldiers|casualties)',
        r'\b\d+\s*(percent|%)',
        r'(increased|decreased|rose|fell)\s+by\s+\d+',
        r'on\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
        r'in\s+\d{4}',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}',
    ]
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize claim extractor."""
        print(f"Loading spaCy model: {model_name}...")
        self.nlp = spacy.load(model_name)
        print("✓ Model loaded")
    
    def extract_claims_from_text(self, text: str) -> List[Dict]:
        """Extract claims from a single text."""
        if not text or not text.strip():
            return []
        
        doc = self.nlp(text)
        claims = []
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            if len(sent_text.split()) < 5:
                continue
            
            has_claim_verb = any(token.lemma_.lower() in self.CLAIM_VERBS for token in sent)
            has_factual_pattern = any(re.search(pattern, sent_text, re.IGNORECASE) for pattern in self.FACTUAL_PATTERNS)
            has_quote = '"' in sent_text or '"' in sent_text or '"' in sent_text
            
            if has_claim_verb or has_factual_pattern or has_quote:
                claim_type = self._classify_claim_type(sent_text, sent)
                
                claims.append({
                    'text': sent_text,
                    'type': claim_type,
                    'has_numbers': self._contains_numbers(sent_text),
                    'has_quote': has_quote,
                    'entities': self._extract_entities(sent),
                    'verifiability_score': self._calculate_verifiability(
                        sent_text, has_claim_verb, has_factual_pattern, has_quote
                    )
                })
        
        claims.sort(key=lambda x: x['verifiability_score'], reverse=True)
        return claims
    
    def _classify_claim_type(self, text: str, sent) -> str:
        """Classify the type of claim."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['accuse', 'alleged', 'blamed']):
            return 'accusation'
        elif any(word in text_lower for word in ['deny', 'denied', 'reject']):
            return 'denial'
        elif re.search(r'\d+\s*(people|casualties|deaths)', text, re.IGNORECASE):
            return 'casualty_report'
        elif re.search(r'\d+\s*percent|%', text):
            return 'statistical'
        elif any(word in text_lower for word in ['will', 'plans to', 'intends to']):
            return 'prediction'
        elif '"' in text:
            return 'quoted_statement'
        else:
            return 'factual_claim'
    
    def _contains_numbers(self, text: str) -> bool:
        """Check if text contains numerical data."""
        return bool(re.search(r'\d+', text))
    
    def _extract_entities(self, sent) -> Dict:
        """Extract named entities from sentence."""
        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],
            'DATE': [],
            'NORP': []
        }
        
        for ent in sent.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)
        
        return {k: v for k, v in entities.items() if v}
    
    def _calculate_verifiability(self, text: str, has_claim_verb: bool, has_factual_pattern: bool, has_quote: bool) -> float:
        """Calculate how verifiable a claim is (0-1 scale)."""
        score = 0.0
        
        if re.search(r'\d+', text):
            score += 0.3
        
        if re.search(r'\d{4}|January|February|March|April|May|June|July|August|September|October|November|December', text, re.IGNORECASE):
            score += 0.2
        
        doc = self.nlp(text)
        if any(ent.label_ in ['PERSON', 'ORG', 'GPE'] for ent in doc.ents):
            score += 0.2
        
        if has_claim_verb:
            score += 0.2
        
        if has_factual_pattern:
            score += 0.1
        
        return min(score, 1.0)
    
    def extract_claims_from_articles(self, articles: List[Dict]) -> List[Dict]:
        """Extract claims from multiple articles."""
        print(f"\nExtracting claims from {len(articles)} articles...")
        
        analyzed_articles = []
        total_claims = 0
        
        for article in articles:
            title_claims = self.extract_claims_from_text(article.get('title', ''))
            desc_claims = self.extract_claims_from_text(article.get('description', ''))
            content_claims = self.extract_claims_from_text(article.get('content', ''))
            
            all_claims = title_claims + desc_claims + content_claims
            unique_claims = self._deduplicate_claims(all_claims)
            
            article_copy = article.copy()
            article_copy['extracted_claims'] = unique_claims
            article_copy['claim_count'] = len(unique_claims)
            
            total_claims += len(unique_claims)
            analyzed_articles.append(article_copy)
        
        print(f"✓ Extracted {total_claims} total claims")
        print(f"✓ Average {total_claims/len(articles):.1f} claims per article")
        
        return analyzed_articles
    
    def _deduplicate_claims(self, claims: List[Dict]) -> List[Dict]:
        """Remove duplicate or very similar claims."""
        if not claims:
            return []
        
        unique = []
        seen_texts = set()
        
        for claim in claims:
            text_normalized = claim['text'].lower().strip()
            
            is_duplicate = False
            for seen in seen_texts:
                words1 = set(text_normalized.split())
                words2 = set(seen.split())
                
                if len(words1) == 0 or len(words2) == 0:
                    continue
                
                overlap = len(words1 & words2) / max(len(words1), len(words2))
                
                if overlap > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(claim)
                seen_texts.add(text_normalized)
        
        return unique
    
    def get_top_claims(self, articles: List[Dict], n: int = 10) -> List[Dict]:
        """Get the top N most verifiable claims across all articles."""
        all_claims = []
        
        for article in articles:
            for claim in article.get('extracted_claims', []):
                all_claims.append({
                    'claim': claim,
                    'source_title': article.get('title', 'Unknown'),
                    'source_url': article.get('url', ''),
                    'source': article.get('source', 'Unknown')
                })
        
        sorted_claims = sorted(all_claims, key=lambda x: x['claim']['verifiability_score'], reverse=True)
        return sorted_claims[:n]


def main():
    """Example usage of ClaimExtractor."""
    
    print("=" * 70)
    print("STAGE 4: CLAIM EXTRACTION")
    print("=" * 70)
    
    input_file = "data/raw/news/test_articles.json"
    
    if not Path(input_file).exists():
        print(f"\n❌ Error: {input_file} not found")
        print("Please run Stage 1 first (news ingestion)")
        return
    
    print(f"\n📂 Loading articles from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        articles = data.get('articles', data)
    
    print(f"✓ Loaded {len(articles)} articles")
    
    extractor = ClaimExtractor()
    analyzed_articles = extractor.extract_claims_from_articles(articles)
    
    print("\n" + "=" * 70)
    print("CLAIM STATISTICS")
    print("=" * 70)
    
    total_claims = sum(a['claim_count'] for a in analyzed_articles)
    print(f"\nTotal claims extracted: {total_claims}")
    print(f"Average claims per article: {total_claims/len(analyzed_articles):.1f}")
    
    top_claims = extractor.get_top_claims(analyzed_articles, n=5)
    
    print("\n" + "=" * 70)
    print("TOP 5 MOST VERIFIABLE CLAIMS")
    print("=" * 70)
    
    for i, item in enumerate(top_claims, 1):
        claim = item['claim']
        print(f"\n[{i}] {claim['text']}")
        print(f"    Type: {claim['type']}")
        print(f"    Verifiability: {claim['verifiability_score']:.2f}")
    
    output_dir = Path("data/processed/claim_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "extracted_claims.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_articles': len(analyzed_articles),
            'total_claims': total_claims,
            'top_claims': top_claims,
            'articles': analyzed_articles
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("✅ CLAIM EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"\n✓ Results saved to: {output_file}")


if __name__ == "__main__":
    main()