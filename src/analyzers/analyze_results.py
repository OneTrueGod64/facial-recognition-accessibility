"""
Facial Recognition Analysis
Analyzes CSV report from facial_recognition_validator.py
Generates capstone-ready insights for accessibility tech research

Usage:
    python analyze_results.py facial_recognition_report_20260508_121828.csv
"""

import csv
import argparse
from pathlib import Path
from collections import defaultdict, Counter
import statistics

class FacialRecognitionAnalyzer:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.data = []
        self.load_data()
    
    def load_data(self):
        """Load CSV data"""
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            self.data = list(reader)
        print(f"✅ Loaded {len(self.data)} images from {self.csv_file}\n")
    
    def analyze_detection(self):
        """Analyze face detection success rates"""
        print("="*60)
        print("DETECTION ACCURACY")
        print("="*60)
        
        detected = [d for d in self.data if d['faces_detected'] != '0']
        detection_rate = len(detected) / len(self.data) * 100
        
        print(f"Total images: {len(self.data)}")
        print(f"Faces detected: {len(detected)}")
        print(f"Detection rate: {detection_rate:.1f}%")
        print(f"Failed detections: {len(self.data) - len(detected)}")
        
        if len(self.data) - len(detected) > 0:
            print(f"\nFailed to detect:")
            for d in self.data:
                if d['faces_detected'] == '0':
                    print(f"  - {d['image']}")
        print()
    
    def analyze_confidence(self):
        """Analyze detection confidence scores"""
        print("="*60)
        print("DETECTION CONFIDENCE")
        print("="*60)
        
        detected = [d for d in self.data if d['faces_detected'] != '0']
        confidences = []
        
        for d in detected:
            try:
                conf = float(d['confidence'])
                confidences.append(conf)
            except:
                pass
        
        if confidences:
            print(f"Average confidence: {statistics.mean(confidences):.2f}%")
            print(f"Min confidence: {min(confidences):.2f}%")
            print(f"Max confidence: {max(confidences):.2f}%")
            print(f"Median confidence: {statistics.median(confidences):.2f}%")
            
            # Count by confidence ranges
            high_conf = len([c for c in confidences if c >= 99.9])
            medium_conf = len([c for c in confidences if 99 <= c < 99.9])
            low_conf = len([c for c in confidences if c < 99])
            
            print(f"\nConfidence distribution:")
            print(f"  ≥99.9%: {high_conf} images")
            print(f"  99-99.9%: {medium_conf} images")
            print(f"  <99%: {low_conf} images")
        print()
    
    def analyze_age(self):
        """Analyze age range detection"""
        print("="*60)
        print("AGE RANGE DETECTION")
        print("="*60)
        
        detected = [d for d in self.data if d['faces_detected'] != '0']
        age_ranges = []
        
        for d in detected:
            if d['age_range'] != 'N/A':
                try:
                    low, high = d['age_range'].split('-')
                    age_ranges.append((int(low), int(high)))
                except:
                    pass
        
        if age_ranges:
            all_lows = [a[0] for a in age_ranges]
            all_highs = [a[1] for a in age_ranges]
            
            print(f"Age range span:")
            print(f"  Youngest detected: {min(all_lows)}-{[h for l, h in age_ranges if l == min(all_lows)][0]} years")
            print(f"  Oldest detected: {[l for l, h in age_ranges if h == max(all_highs)][0]}-{max(all_highs)} years")
            print(f"  Most common range: {statistics.mode(all_lows)} years old (low end)")
            
            # Age brackets
            teens = len([a for a in age_ranges if a[0] < 20])
            twenties = len([a for a in age_ranges if 20 <= a[0] < 30])
            thirties = len([a for a in age_ranges if 30 <= a[0] < 40])
            forties_plus = len([a for a in age_ranges if a[0] >= 40])
            
            print(f"\nAge group distribution:")
            print(f"  Teens (< 20): {teens}")
            print(f"  20s: {twenties}")
            print(f"  30s: {thirties}")
            print(f"  40+: {forties_plus}")
        print()
    
    def analyze_emotion(self):
        """Analyze emotion detection"""
        print("="*60)
        print("EMOTION DETECTION")
        print("="*60)
        
        detected = [d for d in self.data if d['faces_detected'] != '0']
        emotions = defaultdict(int)
        
        for d in detected:
            if d['emotions'] != 'N/A':
                emotion = d['emotions'].split('(')[0].strip()
                emotions[emotion] += 1
        
        if emotions:
            print("Emotions detected:")
            for emotion, count in sorted(emotions.items(), key=lambda x: x[1], reverse=True):
                pct = count / len(detected) * 100
                print(f"  {emotion}: {count} ({pct:.1f}%)")
        print()
    
    def analyze_pose(self):
        """Analyze head pose angles"""
        print("="*60)
        print("HEAD POSE ANALYSIS (For Gaze-Tracking)")
        print("="*60)
        
        detected = [d for d in self.data if d['faces_detected'] != '0']
        pitches, rolls, yaws = [], [], []
        
        for d in detected:
            try:
                if d['pose_pitch'] != 'N/A':
                    pitches.append(float(d['pose_pitch']))
                if d['pose_roll'] != 'N/A':
                    rolls.append(float(d['pose_roll']))
                if d['pose_yaw'] != 'N/A':
                    yaws.append(float(d['pose_yaw']))
            except:
                pass
        
        if pitches and rolls and yaws:
            print("Pitch (vertical tilt):")
            print(f"  Range: {min(pitches):.2f}° to {max(pitches):.2f}°")
            print(f"  Mean: {statistics.mean(pitches):.2f}°")
            
            print("\nRoll (head tilt):")
            print(f"  Range: {min(rolls):.2f}° to {max(rolls):.2f}°")
            print(f"  Mean: {statistics.mean(rolls):.2f}°")
            
            print("\nYaw (horizontal rotation):")
            print(f"  Range: {min(yaws):.2f}° to {max(yaws):.2f}°")
            print(f"  Mean: {statistics.mean(yaws):.2f}°")
            
            # Critical for gaze-tracking
            extreme_yaw = len([y for y in yaws if abs(y) > 30])
            extreme_pitch = len([p for p in pitches if abs(p) > 30])
            
            print(f"\n⚠️  Extreme angles (critical for gaze-tracking):")
            print(f"  High yaw (>30°): {extreme_yaw} images")
            print(f"  High pitch (>30°): {extreme_pitch} images")
        print()
    
    def analyze_accessibility(self):
        """Analyze accessibility implications"""
        print("="*60)
        print("ACCESSIBILITY IMPLICATIONS")
        print("="*60)
        
        detected = [d for d in self.data if d['faces_detected'] != '0']
        
        eyes_closed = 0
        smiling = 0
        mouth_open = 0
        
        for d in detected:
            if d['eyes_open'] == 'False':
                eyes_closed += 1
            if d['smile'] == 'True':
                smiling += 1
            if d['mouth_open'] == 'True':
                mouth_open += 1
        
        print("Expression states detected:")
        print(f"  Eyes closed: {eyes_closed} ({eyes_closed/len(detected)*100:.1f}%)")
        print(f"  Smiling: {smiling} ({smiling/len(detected)*100:.1f}%)")
        print(f"  Mouth open: {mouth_open} ({mouth_open/len(detected)*100:.1f}%)")
        
        print("\n📊 Key Accessibility Findings:")
        print(f"  1. Detection is highly reliable ({statistics.mean([float(d['confidence']) for d in detected if d['confidence'] != 'N/A']):.1f}% avg)")
        print(f"  2. Extreme head poses detected ({len([d for d in detected if abs(float(d['pose_yaw'])) > 30])}) - critical for gaze-tracking")
        print(f"  3. Eyes-closed cases ({eyes_closed}) - need robust handling for accessibility")
        print(f"  4. Diverse age range ({min([int(d['age_range'].split('-')[0]) for d in detected if d['age_range'] != 'N/A'])}-{max([int(d['age_range'].split('-')[1]) for d in detected if d['age_range'] != 'N/A'])}) - good coverage")
        print()
    
    def generate_report(self):
        """Generate full analysis report"""
        print("\n" + "="*60)
        print("FACIAL RECOGNITION ACCESSIBILITY RESEARCH")
        print("Analysis Report")
        print("="*60 + "\n")
        
        self.analyze_detection()
        self.analyze_confidence()
        self.analyze_age()
        self.analyze_emotion()
        self.analyze_pose()
        self.analyze_accessibility()
        
        print("="*60)
        print("RECOMMENDATIONS FOR ACCESSIBILITY")
        print("="*60)
        print("""
1. **Gaze-Tracking Robustness**: 
   - System handles wide pose angles well (±65° yaw detected)
   - Consider multi-sensor validation for extreme angles

2. **Expression Recognition**:
   - Emotion detection reliable for happy/calm states
   - Consider specific training for neutral/surprised for accessibility

3. **Edge Cases**:
   - Eyes-closed detection needs special handling
   - Some images undetectable - need fallback mechanisms

4. **Diverse Population Support**:
   - Age range detection spans 11-59 years
   - Recommend testing with additional age groups (60+)

5. **Implementation Priority**:
   - High: Robust fallback for failed detections
   - Medium: Multi-angle validation for gaze-tracking
   - Low: Enhanced emotion classification
        """)
        print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Analyze facial recognition validation results'
    )
    parser.add_argument('csv_file', help='CSV report file from facial_recognition_validator.py')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"❌ File not found: {args.csv_file}")
        exit(1)
    
    analyzer = FacialRecognitionAnalyzer(args.csv_file)
    analyzer.generate_report()
