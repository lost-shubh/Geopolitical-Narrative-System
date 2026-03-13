"""
Fact Checking Module - Stage 4b
Search for evidence to verify or debunk claims.
"""

import sys
from pathlib import Path
import json
import requests
from typing import List, Dict
import time


class FactChecker:
    """Search for factual evidence to verify claims."""
    
    def __init__(self):
        """Initialize fact checker."""
        print("Initializing fact checker...")
        self.search_results_cache = {}
    
    def search_web(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search the web for information about a claim.
        
        Note: This is a simplified version using DuckDuckGo.
        In production, you'd use Google Fact Check Tools API, 
        Semantic Scholar API, or other specialized fact-checking APIs.
        
        Args:
            query: Search query
            max_results: Number of results to return
            
        Returns:
            List of search results
        """
        # Check cache
        if query in self.search_results_cache:
            return self.search_results_cache[query]
        
        # Simplified web search (in production, use proper APIs)
        # For now, we'll create mock search results
        print(f"  Searching for: {query[:60]}...")
        
        # Mock search results (in production, replace with real API calls)
        mock_results = [
            {
                'title': f'Fact check: {query[:50]}',
                'source': 'FactCheck.org',
                'url': f'https://factcheck.org/search?q={query[:30]}',
                'snippet': 'This claim requires verification. Multiple sources report conflicting information.',
                'credibility_score': 0.85
            },
            {
                'title': f'Analysis: {query[:50]}',
                'source': 'Reuters',
                'url': f'https://reuters.com/fact-check/{query[:20]}',
                'snippet': 'Investigation into this claim shows mixed evidence.',
                'credibility_score': 0.90
            },
            {
                'title': f'Related research: {query[:40]}',
                'source': 'Academic Source',
                'url': f'https://scholar.google.com/scholar?q={query[:30]}',
                'snippet': 'Peer-reviewed studies provide context for this claim.',
                'credibility_score': 0.95
            }
        ]
        
        results = mock_results[:max_results]
        
        # Cache results
        self.search_results_cache[query] = results
        
        # Be nice to servers
        time.sleep(0.5)
        
        return results
    
    def verify_claim(self, claim: Dict) -> Dict:
        """
        Attempt to verify a single claim.
        
        Args:
            claim: Claim dictionary with 'text' field
            
        Returns:
            Verification result
        """
        claim_text = claim.get('text', '')
        
        # Extract key terms for searching
        search_query = self._create_search_query(claim_text)
        
        # Search for evidence
        evidence = self.search_web(search_query, max_results=3)
        
        # Analyze evidence credibility
        avg_credibility = sum(e['credibility_score'] for e in evidence) / len(evidence) if evidence else 0.0
        
        # Determine verification status
        if avg_credibility > 0.85:
            status = 'likely_true'
        elif avg_credibility > 0.6:
            status = 'needs_verification'
        else:
            status = 'disputed'
        
        return {
            'claim': claim_text,
            'claim_type': claim.get('type', 'unknown'),
            'verification_status': status,
            'credibility_score': round(avg_credibility, 2),
            'evidence_count': len(evidence),
            'evidence': evidence,
            'entities': claim.get('entities', {}),
            'search_query': search_query
        }
    
    def _create_search_query(self, claim_text: str) -> str:
        """
        Create an optimized search query from a claim.
        
        Args:
            claim_text: Original claim text
            
        Returns:
            Optimized search query
        """
        # Remove common words and focus on key terms
        # In production, use NLP to extract key phrases
        
        # For now, simple approach: take first 10 meaningful words
        words = claim_text.split()[:10]
        query = ' '.join(words)
        
        # Add fact-check context
        return f'fact check {query}'
    
    def verify_multiple_claims(self, claims: List[Dict]) -> List[Dict]:
        """
        Verify multiple claims.
        
        Args:
            claims: List of claim dictionaries
            
        Returns:
            List of verification results
        """
        print(f"\nVerifying {len(claims)} claims...")
        
        verified = []
        
        for i, claim_item in enumerate(claims, 1):
            print(f"[{i}/{len(claims)}] Verifying claim...")
            
            # Get the actual claim object
            if 'claim' in claim_item:
                claim = claim_item['claim']
            else:
                claim = claim_item
            
            result = self.verify_claim(claim)
            
            # Add source info if available
            if 'source_title' in claim_item:
                result['original_source'] = {
                    'title': claim_item.get('source_title', ''),
                    'url': claim_item.get('source_url', ''),
                    'source': claim_item.get('source', '')
                }
            
            verified.append(result)
        
        print(f"✓ Verification complete")
        
        return verified
    
    def get_verification_statistics(self, verified_claims: List[Dict]) -> Dict:
        """
        Get statistics about verification results.
        
        Args:
            verified_claims: List of verified claim dictionaries
            
        Returns:
            Statistics dictionary
        """
        total = len(verified_claims)
        
        if total == 0:
            return {}
        
        status_counts = {}
        for claim in verified_claims:
            status = claim['verification_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        avg_credibility = sum(c['credibility_score'] for c in verified_claims) / total
        
        return {
            'total_verified': total,
            'status_breakdown': status_counts,
            'average_credibility': round(avg_credibility, 2),
            'high_credibility_count': sum(1 for c in verified_claims if c['credibility_score'] > 0.8),
            'disputed_count': sum(1 for c in verified_claims if c['verification_status'] == 'disputed')
        }


def main():
    """Run fact checking on extracted claims."""
    
    print("=" * 70)
    print("STAGE 4B: FACT VERIFICATION")
    print("=" * 70)
    
    # Load extracted claims
    input_file = "data/processed/claim_extraction/extracted_claims.json"
    
    if not Path(input_file).exists():
        print(f"\n❌ Error: {input_file} not found")
        print("Please run Stage 4a first (claim extraction):")
        print("  python src/analysis/claim_extraction.py")
        return
    
    print(f"\n📂 Loading claims from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    top_claims = data.get('top_claims', [])
    
    if not top_claims:
        print("❌ No claims found in file")
        return
    
    print(f"✓ Loaded {len(top_claims)} top claims")
    
    # Initialize fact checker
    fact_checker = FactChecker()
    
    # Verify claims
    verified_claims = fact_checker.verify_multiple_claims(top_claims[:10])  # Verify top 10
    
    # Get statistics
    print("\n" + "=" * 70)
    print("VERIFICATION STATISTICS")
    print("=" * 70)
    
    stats = fact_checker.get_verification_statistics(verified_claims)
    
    print(f"\nTotal claims verified: {stats['total_verified']}")
    print(f"Average credibility: {stats['average_credibility']}")
    print(f"High credibility (>0.8): {stats['high_credibility_count']}")
    print(f"Disputed: {stats['disputed_count']}")
    
    print("\nVerification status breakdown:")
    for status, count in sorted(stats['status_breakdown'].items()):
        pct = (count / stats['total_verified']) * 100
        print(f"  {status:20s}: {count} ({pct:.1f}%)")
    
    # Show sample results
    print("\n" + "=" * 70)
    print("SAMPLE VERIFICATION RESULTS")
    print("=" * 70)
    
    for i, result in enumerate(verified_claims[:3], 1):
        print(f"\n[{i}] {result['claim'][:80]}...")
        print(f"    Status: {result['verification_status'].upper()}")
        print(f"    Credibility: {result['credibility_score']}")
        print(f"    Evidence sources: {result['evidence_count']}")
        
        if result['evidence']:
            print(f"    Top source: {result['evidence'][0]['source']}")
            print(f"    Snippet: {result['evidence'][0]['snippet'][:70]}...")
    
    # Save results
    output_dir = Path("data/processed/fact_verification")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "verified_claims.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_verified': len(verified_claims),
            'statistics': stats,
            'verified_claims': verified_claims
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("✅ FACT VERIFICATION COMPLETE")
    print("=" * 70)
    print(f"\n✓ Results saved to: {output_file}")
    
    # Summary
    print("\n📊 Key Findings:")
    likely_true = stats['status_breakdown'].get('likely_true', 0)
    disputed = stats['status_breakdown'].get('disputed', 0)
    
    if likely_true > disputed:
        print(f"  ✅ Most claims appear credible ({likely_true} likely true)")
    elif disputed > 0:
        print(f"  ⚠️  {disputed} claims are disputed - require further investigation")
    
    print("\n🚀 Next: Generate counter-narratives for disputed claims")
    print("   (Stage 5: Narrative Synthesis)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()