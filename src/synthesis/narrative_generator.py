"""
Narrative Synthesis Module - Stage 5
Generates evidence-based counter-narratives for disputed claims.
"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class NarrativeGenerator:
    """Generate counter-narratives based on fact-checking results."""
    
    # Templates for different claim types
    TEMPLATES = {
        'accusation': {
            'intro': "Regarding the claim that {claim}, our analysis shows:",
            'evidence_section': "Evidence from {source_count} sources indicates:",
            'conclusion': "Conclusion: {verdict}"
        },
        'statistical': {
            'intro': "The statistical claim states: {claim}",
            'evidence_section': "Verification against {source_count} authoritative sources:",
            'conclusion': "Assessment: {verdict}"
        },
        'casualty_report': {
            'intro': "Concerning casualty reports claiming {claim}:",
            'evidence_section': "Cross-referenced with {source_count} independent sources:",
            'conclusion': "Verified status: {verdict}"
        },
        'default': {
            'intro': "Claim: {claim}",
            'evidence_section': "After reviewing {source_count} sources:",
            'conclusion': "Finding: {verdict}"
        }
    }
    
    def __init__(self):
        """Initialize narrative generator."""
        print("Initializing narrative generator...")
    
    def generate_verdict(self, verification_status: str, credibility_score: float) -> str:
        """
        Generate a verdict statement based on verification results.
        
        Args:
            verification_status: Status from fact checker
            credibility_score: Credibility score (0-1)
            
        Returns:
            Verdict statement
        """
        if verification_status == 'likely_true':
            if credibility_score > 0.9:
                return "This claim is strongly supported by available evidence"
            else:
                return "This claim appears credible based on current evidence"
        
        elif verification_status == 'disputed':
            return "This claim is disputed by multiple credible sources and requires correction"
        
        else:  # needs_verification
            return "This claim requires additional verification from independent sources"
    
    def generate_evidence_summary(self, evidence: List[Dict]) -> List[str]:
        """
        Create bullet points summarizing evidence.
        
        Args:
            evidence: List of evidence dictionaries
            
        Returns:
            List of evidence summary strings
        """
        summaries = []
        
        for i, item in enumerate(evidence[:3], 1):  # Top 3 sources
            source = item.get('source', 'Unknown source')
            credibility = item.get('credibility_score', 0)
            snippet = item.get('snippet', 'No description available')
            
            summary = f"• {source} (credibility: {credibility:.2f}): {snippet[:100]}..."
            summaries.append(summary)
        
        return summaries
    
    def generate_counter_narrative(self, verified_claim: Dict) -> Dict:
        """
        Generate a complete counter-narrative for a verified claim.
        
        Args:
            verified_claim: Claim with verification results
            
        Returns:
            Counter-narrative document
        """
        claim_text = verified_claim.get('claim', '')
        claim_type = verified_claim.get('claim_type', 'default')
        status = verified_claim.get('verification_status', 'needs_verification')
        credibility = verified_claim.get('credibility_score', 0)
        evidence = verified_claim.get('evidence', [])
        
        # Select template
        template = self.TEMPLATES.get(claim_type, self.TEMPLATES['default'])
        
        # Build narrative sections
        intro = template['intro'].format(claim=claim_text[:100])
        
        evidence_header = template['evidence_section'].format(
            source_count=len(evidence)
        )
        
        evidence_bullets = self.generate_evidence_summary(evidence)
        
        verdict = self.generate_verdict(status, credibility)
        conclusion = template['conclusion'].format(verdict=verdict)
        
        # Compile full narrative
        narrative_parts = [
            intro,
            "",
            evidence_header,
            *evidence_bullets,
            "",
            conclusion
        ]
        
        narrative_text = "\n".join(narrative_parts)
        
        # Add metadata
        return {
            'original_claim': claim_text,
            'claim_type': claim_type,
            'verification_status': status,
            'credibility_score': credibility,
            'counter_narrative': narrative_text,
            'evidence_count': len(evidence),
            'generated_at': datetime.now().isoformat(),
            'confidence': 'high' if credibility > 0.8 else 'medium' if credibility > 0.6 else 'low'
        }
    
    def generate_multiple_narratives(self, verified_claims: List[Dict]) -> List[Dict]:
        """
        Generate counter-narratives for multiple claims.
        
        Args:
            verified_claims: List of verified claim dictionaries
            
        Returns:
            List of counter-narrative documents
        """
        print(f"\nGenerating counter-narratives for {len(verified_claims)} claims...")
        
        narratives = []
        
        for i, claim in enumerate(verified_claims, 1):
            print(f"[{i}/{len(verified_claims)}] Generating narrative...")
            narrative = self.generate_counter_narrative(claim)
            narratives.append(narrative)
        
        print(f"✓ Generated {len(narratives)} counter-narratives")
        
        return narratives
    
    def create_summary_report(self, narratives: List[Dict]) -> str:
        """
        Create a human-readable summary report.
        
        Args:
            narratives: List of counter-narrative documents
            
        Returns:
            Formatted report text
        """
        report_lines = [
            "=" * 70,
            "COUNTER-NARRATIVE SYNTHESIS REPORT",
            "=" * 70,
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total narratives: {len(narratives)}",
            ""
        ]
        
        # Statistics
        high_conf = sum(1 for n in narratives if n['confidence'] == 'high')
        disputed = sum(1 for n in narratives if n['verification_status'] == 'disputed')
        
        report_lines.extend([
            "SUMMARY:",
            f"  High confidence narratives: {high_conf}",
            f"  Disputed claims addressed: {disputed}",
            ""
        ])
        
        # Individual narratives
        report_lines.append("=" * 70)
        report_lines.append("COUNTER-NARRATIVES")
        report_lines.append("=" * 70)
        
        for i, narrative in enumerate(narratives, 1):
            report_lines.extend([
                "",
                f"[{i}] " + "=" * 65,
                f"CLAIM: {narrative['original_claim'][:80]}...",
                f"STATUS: {narrative['verification_status'].upper()}",
                f"CONFIDENCE: {narrative['confidence'].upper()}",
                "",
                narrative['counter_narrative'],
                ""
            ])
        
        return "\n".join(report_lines)


def main():
    """Generate counter-narratives from verified claims."""
    
    print("=" * 70)
    print("STAGE 5: NARRATIVE SYNTHESIS")
    print("=" * 70)
    
    # Load verified claims
    input_file = "data/processed/fact_verification/verified_claims.json"
    
    if not Path(input_file).exists():
        print(f"\n❌ Error: {input_file} not found")
        print("Please run Stage 4 first:")
        print("  python test_claim_verification.py")
        return
    
    print(f"\n📂 Loading verified claims from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    verified_claims = data.get('verified_claims', [])
    
    if not verified_claims:
        print("❌ No verified claims found")
        return
    
    print(f"✓ Loaded {len(verified_claims)} verified claims")
    
    # Initialize generator
    generator = NarrativeGenerator()
    
    # Generate narratives
    narratives = generator.generate_multiple_narratives(verified_claims)
    
    # Show sample
    print("\n" + "=" * 70)
    print("SAMPLE COUNTER-NARRATIVE")
    print("=" * 70)
    
    if narratives:
        sample = narratives[0]
        print(f"\nOriginal Claim:")
        print(f"  {sample['original_claim'][:100]}...")
        print(f"\nVerification Status: {sample['verification_status'].upper()}")
        print(f"Confidence: {sample['confidence'].upper()}")
        print(f"\nCounter-Narrative:")
        print("  " + sample['counter_narrative'].replace('\n', '\n  '))
    
    # Create report
    print("\n" + "=" * 70)
    print("GENERATING REPORT")
    print("=" * 70)
    
    report_text = generator.create_summary_report(narratives)
    
    # Save results
    output_dir = Path("data/processed/narrative_synthesis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_file = output_dir / "counter_narratives.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_narratives': len(narratives),
            'generated_at': datetime.now().isoformat(),
            'narratives': narratives
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON results saved to: {json_file}")
    
    # Save report
    report_file = output_dir / "COUNTER_NARRATIVE_REPORT.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"✓ Report saved to: {report_file}")
    
    # Statistics
    print("\n" + "=" * 70)
    print("STATISTICS")
    print("=" * 70)
    
    high_conf = sum(1 for n in narratives if n['confidence'] == 'high')
    medium_conf = sum(1 for n in narratives if n['confidence'] == 'medium')
    low_conf = sum(1 for n in narratives if n['confidence'] == 'low')
    
    print(f"\nConfidence levels:")
    print(f"  High:   {high_conf} ({high_conf/len(narratives)*100:.1f}%)")
    print(f"  Medium: {medium_conf} ({medium_conf/len(narratives)*100:.1f}%)")
    print(f"  Low:    {low_conf} ({low_conf/len(narratives)*100:.1f}%)")
    
    disputed = sum(1 for n in narratives if n['verification_status'] == 'disputed')
    if disputed > 0:
        print(f"\n⚠️  {disputed} claims identified as disputed")
        print("   These require priority correction")
    
    print("\n" + "=" * 70)
    print("✅ NARRATIVE SYNTHESIS COMPLETE")
    print("=" * 70)
    
    print(f"\n📄 Read the full report:")
    print(f"   {report_file}")
    
    print("\n🎉 ALL STAGES COMPLETE!")
    print("\nYour complete analysis pipeline:")
    print("  ✅ Stage 1: News ingestion")
    print("  ✅ Stage 2: Social media data")
    print("  ✅ Stage 3: Sentiment & emotion analysis")
    print("  ✅ Stage 4: Claim extraction & verification")
    print("  ✅ Stage 5: Counter-narrative synthesis")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()