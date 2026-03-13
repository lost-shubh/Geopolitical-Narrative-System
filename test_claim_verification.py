"""
Test script for Stage 4 - Claim Extraction & Fact Verification
Runs both extraction and verification in sequence.
"""

import sys
from pathlib import Path
import json

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(src_path / "analysis"))
sys.path.insert(0, str(src_path / "verification"))

from claim_extraction import ClaimExtractor
from fact_checker import FactChecker


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    """Run complete claim extraction and verification pipeline."""
    
    print_header("STAGE 4: CLAIM EXTRACTION & FACT VERIFICATION")
    
    # ===== PART 1: CLAIM EXTRACTION =====
    print_header("PART 1: EXTRACTING CLAIMS FROM NEWS")
    
    # Load articles
    input_file = "data/raw/news/test_articles.json"
    
    if not Path(input_file).exists():
        print(f"\n❌ Error: {input_file} not found")
        print("Please run Stage 1 first:")
        print("  python test_news_ingestion.py")
        return
    
    print(f"\n📂 Loading articles from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        articles = data.get('articles', data)
    
    print(f"✓ Loaded {len(articles)} articles")
    
    # Extract claims
    print("\n🔄 Initializing claim extractor...")
    extractor = ClaimExtractor()
    
    print("🔍 Extracting claims...")
    analyzed_articles = extractor.extract_claims_from_articles(articles)
    
    # Statistics
    total_claims = sum(a['claim_count'] for a in analyzed_articles)
    print(f"\n✓ Extracted {total_claims} total claims")
    print(f"✓ Average {total_claims/len(analyzed_articles):.1f} claims per article")
    
    # Get top claims
    top_claims = extractor.get_top_claims(analyzed_articles, n=10)
    
    print("\n📌 Top 5 most verifiable claims:")
    for i, item in enumerate(top_claims[:5], 1):
        claim = item['claim']
        print(f"\n[{i}] {claim['text'][:70]}...")
        print(f"    Type: {claim['type']}")
        print(f"    Verifiability: {claim['verifiability_score']:.2f}")
        print(f"    Source: {item['source']}")
    
    # Save extraction results
    output_dir = Path("data/processed/claim_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extraction_file = output_dir / "extracted_claims.json"
    with open(extraction_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_articles': len(analyzed_articles),
            'total_claims': total_claims,
            'top_claims': top_claims,
            'articles': analyzed_articles
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Extraction results saved to: {extraction_file}")
    
    # ===== PART 2: FACT VERIFICATION =====
    print_header("PART 2: VERIFYING CLAIMS")
    
    print("\n🔄 Initializing fact checker...")
    fact_checker = FactChecker()
    
    print(f"🔍 Verifying top {min(10, len(top_claims))} claims...")
    print("   (Note: Using mock fact-checking for demonstration)")
    print("   (In production: Would use Google Fact Check Tools API, etc.)\n")
    
    verified_claims = fact_checker.verify_multiple_claims(top_claims[:10])
    
    # Statistics
    stats = fact_checker.get_verification_statistics(verified_claims)
    
    print("\n" + "=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)
    
    print(f"\nTotal claims verified: {stats['total_verified']}")
    print(f"Average credibility score: {stats['average_credibility']}")
    print(f"High credibility (>0.8): {stats['high_credibility_count']}")
    print(f"Disputed claims: {stats['disputed_count']}")
    
    print("\nStatus breakdown:")
    for status, count in sorted(stats['status_breakdown'].items()):
        pct = (count / stats['total_verified']) * 100
        status_emoji = {
            'likely_true': '✅',
            'needs_verification': '⚠️',
            'disputed': '❌'
        }.get(status, '❓')
        
        print(f"  {status_emoji} {status:20s}: {count} ({pct:.1f}%)")
    
    # Show detailed results for top 3
    print("\n" + "=" * 70)
    print("DETAILED VERIFICATION (Top 3 Claims)")
    print("=" * 70)
    
    for i, result in enumerate(verified_claims[:3], 1):
        print(f"\n{'='*70}")
        print(f"CLAIM {i}")
        print(f"{'='*70}")
        print(f"\n📝 {result['claim']}")
        print(f"\n📊 Verification:")
        print(f"   Status: {result['verification_status'].upper()}")
        print(f"   Credibility: {result['credibility_score']}/1.00")
        print(f"   Type: {result['claim_type']}")
        
        if result.get('entities'):
            print(f"\n🏷️  Entities mentioned:")
            for entity_type, entities in result['entities'].items():
                print(f"   {entity_type}: {', '.join(entities[:3])}")
        
        print(f"\n🔍 Evidence found ({result['evidence_count']} sources):")
        for j, evidence in enumerate(result['evidence'][:2], 1):
            print(f"\n   [{j}] {evidence['source']}")
            print(f"       {evidence['snippet'][:80]}...")
            print(f"       Credibility: {evidence['credibility_score']:.2f}")
            print(f"       URL: {evidence['url'][:60]}...")
    
    # Save verification results
    verification_dir = Path("data/processed/fact_verification")
    verification_dir.mkdir(parents=True, exist_ok=True)
    
    verification_file = verification_dir / "verified_claims.json"
    with open(verification_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_verified': len(verified_claims),
            'statistics': stats,
            'verified_claims': verified_claims
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Verification results saved to: {verification_file}")
    
    # ===== FINAL SUMMARY =====
    print_header("✅ STAGE 4 COMPLETE")
    
    print("\n📁 Files created:")
    print(f"  1. {extraction_file}")
    print(f"  2. {verification_file}")
    
    print("\n📊 Summary:")
    print(f"  • Extracted {total_claims} claims from {len(articles)} articles")
    print(f"  • Verified {len(verified_claims)} top claims")
    print(f"  • {stats['high_credibility_count']} claims have high credibility")
    print(f"  • {stats['disputed_count']} claims need further investigation")
    
    print("\n💡 Key Insights:")
    
    # Insight 1: Claim density
    avg_claims = total_claims / len(articles)
    if avg_claims > 5:
        print(f"  ⚠️  High claim density ({avg_claims:.1f} per article) - intense news cycle")
    else:
        print(f"  ✓ Normal claim density ({avg_claims:.1f} per article)")
    
    # Insight 2: Verification status
    likely_true = stats['status_breakdown'].get('likely_true', 0)
    disputed = stats['status_breakdown'].get('disputed', 0)
    
    if disputed > likely_true:
        print(f"  ⚠️  More disputed than verified claims - potential misinformation")
    elif likely_true > 0:
        print(f"  ✓ Most claims appear credible")
    
    # Insight 3: Needs verification
    needs_verification = stats['status_breakdown'].get('needs_verification', 0)
    if needs_verification > 0:
        print(f"  📋 {needs_verification} claims require additional fact-checking")
    
    print("\n🚀 Next Steps:")
    print("  1. Review disputed claims in detail")
    print("  2. Cross-reference with additional fact-checking sources")
    print("  3. Generate counter-narratives for false claims")
    print("  4. Ready for Stage 5? Tell me: 'Build Stage 5 - Narrative Synthesis'")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()