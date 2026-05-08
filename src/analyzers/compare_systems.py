"""
Multi-System Comparison Analyzer
Analyzes CSV output from multi_system_validator.py
Compares accuracy, agreement, and failure modes across AWS, Google, Azure

Usage:
    python compare_systems.py multi_system_report_*.csv
"""

import csv
import argparse
from pathlib import Path
from collections import defaultdict
import statistics
from typing import Dict, List

class MultiSystemComparator:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.data = []
        self.load_data()
    
    def load_data(self):
        """Load CSV results"""
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            self.data = list(reader)
        print(f"✅ Loaded {len(self.data)} image comparisons\n")
    
    def analyze_detection_rates(self):
        """Compare detection rates across systems"""
        print("="*80)
        print("DETECTION RATE COMPARISON")
        print("="*80)
        
        systems = ['aws', 'google', 'azure']
        detection_counts = {sys: 0 for sys in systems}
        total = len(self.data)
        
        for row in self.data:
            for system in systems:
                status_key = f'{system}_status'
                if status_key in row:
                    if row[status_key] == 'success':
                        detection_counts[system] += 1
        
        print(f"\nTotal images tested: {total}\n")
        for system in systems:
            count = detection_counts[system]
            rate = count / total * 100 if total > 0 else 0
            print(f"  {system.upper():8} {count:3}/{total} = {rate:5.1f}%")
        
        print()
    
    def analyze_confidence(self):
        """Compare confidence scores"""
        print("="*80)
        print("CONFIDENCE ANALYSIS")
        print("="*80)
        
        confidences = {'aws': [], 'google': [], 'azure': []}
        
        for row in self.data:
            # AWS confidence
            if 'aws_confidence' in row and row['aws_confidence'] and row['aws_status'] == 'success':
                try:
                    confidences['aws'].append(float(row['aws_confidence']))
                except:
                    pass
            
            # Google confidence
            if 'google_confidence' in row and row['google_confidence'] and row['google_status'] == 'success':
                try:
                    confidences['google'].append(float(row['google_confidence']))
                except:
                    pass
            
            # Azure confidence
            if 'azure_confidence' in row and row['azure_confidence'] and row['azure_status'] == 'success':
                try:
                    confidences['azure'].append(float(row['azure_confidence']))
                except:
                    pass
        
        print()
        for system, scores in confidences.items():
            if scores:
                print(f"  {system.upper()}:")
                print(f"    Average:  {statistics.mean(scores):.2f}%")
                print(f"    Median:   {statistics.median(scores):.2f}%")
                print(f"    Min/Max:  {min(scores):.2f}% - {max(scores):.2f}%")
            else:
                print(f"  {system.upper()}: No data")
        
        print()
    
    def analyze_agreement(self):
        """Analyze system agreement on same images"""
        print("="*80)
        print("SYSTEM AGREEMENT ANALYSIS")
        print("="*80)
        
        # Count cases where systems agree on detection
        both_detected = 0
        aws_only = 0
        google_only = 0
        azure_only = 0
        none_detected = 0
        
        for row in self.data:
            aws_ok = row.get('aws_status') == 'success'
            google_ok = row.get('google_status') == 'success'
            azure_ok = row.get('azure_status') == 'success'
            
            if aws_ok and google_ok and azure_ok:
                both_detected += 1
            elif aws_ok:
                aws_only += 1
            elif google_ok:
                google_only += 1
            elif azure_ok:
                azure_only += 1
            else:
                none_detected += 1
        
        total = len(self.data)
        
        print(f"\nAll three detected:  {both_detected:3} ({both_detected/total*100:5.1f}%)")
        print(f"AWS only:            {aws_only:3} ({aws_only/total*100:5.1f}%)")
        print(f"Google only:         {google_only:3} ({google_only/total*100:5.1f}%)")
        print(f"Azure only:          {azure_only:3} ({azure_only/total*100:5.1f}%)")
        print(f"None detected:       {none_detected:3} ({none_detected/total*100:5.1f}%)")
        print()
    
    def analyze_age_detection(self):
        """Compare age detection consistency"""
        print("="*80)
        print("AGE DETECTION CONSISTENCY")
        print("="*80)
        
        age_ranges = []
        
        for row in self.data:
            if row.get('aws_status') == 'success':
                try:
                    low = int(row.get('aws_age_low', 0))
                    high = int(row.get('aws_age_high', 0))
                    if low > 0:
                        age_ranges.append((low, high))
                except:
                    pass
        
        if age_ranges:
            lows = [a[0] for a in age_ranges]
            highs = [a[1] for a in age_ranges]
            
            print(f"\nAWS Age Detection (from {len(age_ranges)} successful detections):")
            print(f"  Average age range: {statistics.mean(lows):.1f}-{statistics.mean(highs):.1f} years")
            print(f"  Youngest: {min(lows)}-{[h for l, h in age_ranges if l == min(lows)][0]}")
            print(f"  Oldest:   {[l for l, h in age_ranges if h == max(highs)][0]}-{max(highs)}")
        
        print()
    
    def analyze_failures(self):
        """Identify failure patterns"""
        print("="*80)
        print("FAILURE ANALYSIS")
        print("="*80)
        
        failures = []
        
        for row in self.data:
            if row.get('aws_status') == 'no_faces' or row.get('google_status') == 'no_faces' or row.get('azure_status') == 'no_faces':
                failures.append(row['image'])
        
        if failures:
            print(f"\n{len(failures)} images failed detection:")
            for img in failures[:10]:  # Show first 10
                print(f"  - {Path(img).name}")
            if len(failures) > 10:
                print(f"  ... and {len(failures) - 10} more")
        else:
            print("\n✅ All images detected successfully")
        
        print()
    
    def analyze_accessibility(self):
        """Analyze accessibility implications"""
        print("="*80)
        print("ACCESSIBILITY IMPLICATIONS")
        print("="*80)
        
        # Eyes open/closed states
        eyes_closed_aws = 0
        eyes_open_aws = 0
        mouth_open_aws = 0
        smiling_aws = 0
        
        for row in self.data:
            if row.get('aws_status') == 'success':
                if row.get('aws_eyes_open') == 'False':
                    eyes_closed_aws += 1
                else:
                    eyes_open_aws += 1
                
                if row.get('aws_mouth_open') == 'True':
                    mouth_open_aws += 1
                
                if row.get('aws_smile') == 'True':
                    smiling_aws += 1
        
        total_aws = eyes_closed_aws + eyes_open_aws
        
        if total_aws > 0:
            print(f"\nExpression Detection (AWS, {total_aws} faces):")
            print(f"  Eyes open:   {eyes_open_aws:3} ({eyes_open_aws/total_aws*100:5.1f}%)")
            print(f"  Eyes closed: {eyes_closed_aws:3} ({eyes_closed_aws/total_aws*100:5.1f}%)")
            print(f"  Mouth open:  {mouth_open_aws:3} ({mouth_open_aws/total_aws*100:5.1f}%)")
            print(f"  Smiling:     {smiling_aws:3} ({smiling_aws/total_aws*100:5.1f}%)")
            
            print(f"\n⚠️  Critical for Accessibility:")
            print(f"    Eyes-closed rate: {eyes_closed_aws/total_aws*100:.1f}%")
            print(f"    → Need fallback for eye-tracking when eyes closed")
        
        print()
    
    def generate_report(self):
        """Generate full comparative analysis"""
        print("\n" + "="*80)
        print("MULTI-SYSTEM FACIAL RECOGNITION COMPARISON")
        print("Research Analysis Report")
        print("="*80 + "\n")
        
        self.analyze_detection_rates()
        self.analyze_confidence()
        self.analyze_agreement()
        self.analyze_age_detection()
        self.analyze_failures()
        self.analyze_accessibility()
        
        print("="*80)
        print("RESEARCH RECOMMENDATIONS")
        print("="*80)
        print("""
1. **System Selection**:
   - Which system has highest detection rate?
   - Which has highest confidence scores?
   - Which is most reliable for accessibility scenarios?

2. **Failure Modes**:
   - What images fail across all systems?
   - Can we predict failures based on image characteristics?
   - What are the accessibility implications?

3. **Complementary Systems**:
   - Could combining systems (vote on detection) improve robustness?
   - Does one system excel where another fails?

4. **Accessibility Gaps**:
   - Eye-tracking systems need eyes-open detection
   - Expression-based communication needs emotion recognition
   - Gaze-tracking needs robust head pose estimation

5. **Next Phase**:
   - Test with actual accessibility device scenarios
   - Implement fallback mechanisms for detected edge cases
   - Expand dataset to more diverse populations
        """)
        print("="*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compare multi-system facial recognition results'
    )
    parser.add_argument('csv_file', help='CSV report from multi_system_validator.py')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"❌ File not found: {args.csv_file}")
        exit(1)
    
    comparator = MultiSystemComparator(args.csv_file)
    comparator.generate_report()
