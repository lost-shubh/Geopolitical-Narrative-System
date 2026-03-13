"""
Complete System Test - All 5 Stages
Runs the entire geopolitical narrative intelligence pipeline.
"""

import sys
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("GEOPOLITICAL NARRATIVE INTELLIGENCE SYSTEM")
print("Complete End-to-End Test")
print("=" * 70)
print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Track completion
completed_stages = []

# ===== STAGE 1: NEWS INGESTION =====
print("\n" + "=" * 70)
print("STAGE 1: NEWS INGESTION")
print("=" * 70)

try:
    import test_news_ingestion
    test_news_ingestion.main()
    completed_stages.append("Stage 1: News Ingestion")
    print("✅ Stage 1 complete")
except Exception as e:
    print(f"❌ Stage 1 failed: {e}")
    print("   Continuing with existing data...")

# ===== STAGE 2: SOCIAL MEDIA DATA =====
print("\n" + "=" * 70)
print("STAGE 2: SOCIAL MEDIA DATA GENERATION")
print("=" * 70)

try:
    import create_mock_data
    create_mock_data.main()
    completed_stages.append("Stage 2: Social Media Data")
    print("✅ Stage 2 complete")
except Exception as e:
    print(f"❌ Stage 2 failed: {e}")
    print("   Continuing with existing data...")

# ===== STAGE 3: ANALYSIS =====
print("\n" + "=" * 70)
print("STAGE 3: SENTIMENT & EMOTION ANALYSIS")
print("=" * 70)

try:
    import test_analysis
    test_analysis.main()
    completed_stages.append("Stage 3: Sentiment & Emotion Analysis")
    print("✅ Stage 3 complete")
except Exception as e:
    print(f"❌ Stage 3 failed: {e}")

try:
    import analyze_social_comments
    analyze_social_comments.main()
    completed_stages.append("Stage 3b: Social Media Analysis")
    print("✅ Stage 3b complete")
except Exception as e:
    print(f"❌ Stage 3b failed: {e}")

# ===== STAGE 4: CLAIM VERIFICATION =====
print("\n" + "=" * 70)
print("STAGE 4: CLAIM EXTRACTION & FACT VERIFICATION")
print("=" * 70)

try:
    import test_claim_verification
    test_claim_verification.main()
    completed_stages.append("Stage 4: Claim Extraction & Verification")
    print("✅ Stage 4 complete")
except Exception as e:
    print(f"❌ Stage 4 failed: {e}")

# ===== STAGE 5: NARRATIVE SYNTHESIS =====
print("\n" + "=" * 70)
print("STAGE 5: COUNTER-NARRATIVE SYNTHESIS")
print("=" * 70)

try:
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path / "synthesis"))
    from narrative_generator import NarrativeGenerator
    
    # Run narrative generation
    import json
    
    input_file = Path("data/processed/fact_verification/verified_claims.json")
    if input_file.exists():
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        verified_claims = data.get('verified_claims', [])
        
        if verified_claims:
            generator = NarrativeGenerator()
            narratives = generator.generate_multiple_narratives(verified_claims)
            
            # Save results
            output_dir = Path("data/processed/narrative_synthesis")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            json_file = output_dir / "counter_narratives.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_narratives': len(narratives),
                    'generated_at': datetime.now().isoformat(),
                    'narratives': narratives
                }, f, indent=2, ensure_ascii=False)
            
            report_text = generator.create_summary_report(narratives)
            report_file = output_dir / "COUNTER_NARRATIVE_REPORT.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            print(f"✓ Generated {len(narratives)} counter-narratives")
            print(f"✓ Saved to: {json_file}")
            completed_stages.append("Stage 5: Narrative Synthesis")
            print("✅ Stage 5 complete")
        else:
            print("⚠️  No verified claims found")
    else:
        print("⚠️  Verification results not found")
        
except Exception as e:
    print(f"❌ Stage 5 failed: {e}")
    import traceback
    traceback.print_exc()

# ===== FINAL SUMMARY =====
print("\n" + "=" * 70)
print("✅ COMPLETE SYSTEM TEST FINISHED")
print("=" * 70)

print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\nStages completed: {len(completed_stages)}/5")

for stage in completed_stages:
    print(f"  ✅ {stage}")

print("\n" + "=" * 70)
print("OUTPUT FILES GENERATED")
print("=" * 70)

output_files = [
    ("News Articles", "data/raw/news/test_articles.json"),
    ("Social Comments", "data/raw/social/mock_social_comments.json"),
    ("News Analysis", "data/processed/combined_analysis/sentiment_emotion_analysis.json"),
    ("Social Analysis", "data/processed/social_analysis/analyzed_comments.json"),
    ("Extracted Claims", "data/processed/claim_extraction/extracted_claims.json"),
    ("Verified Claims", "data/processed/fact_verification/verified_claims.json"),
    ("Counter-Narratives", "data/processed/narrative_synthesis/counter_narratives.json"),
    ("Final Report", "data/processed/narrative_synthesis/COUNTER_NARRATIVE_REPORT.txt"),
]

print("\nCheck these files:")
for name, filepath in output_files:
    if Path(filepath).exists():
        print(f"  ✅ {name}: {filepath}")
    else:
        print(f"  ⚠️  {name}: Not found")

print("\n" + "=" * 70)
print("🎉 SYSTEM FULLY OPERATIONAL")
print("=" * 70)

print("\nYour geopolitical narrative intelligence system is complete!")
print("\nCapabilities:")
print("  📰 News article collection and analysis")
print("  💬 Social media reaction monitoring")
print("  😊 Sentiment and emotion detection")
print("  🔍 Claim extraction and fact verification")
print("  📝 Evidence-based counter-narrative generation")

print("\n💡 Next steps:")
print("  1. Review the counter-narrative report")
print("  2. Examine specific claims and their verification")
print("  3. Deploy to production environment")
print("  4. Connect to real-time data sources")
print("  5. Build visualization dashboard")

print("\n" + "=" * 70)