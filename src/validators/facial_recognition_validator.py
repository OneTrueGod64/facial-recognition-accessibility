"""
Facial Recognition Validation Framework
Tests AWS Rekognition accuracy across diverse face types
Built for accessibility tech research - documenting where systems fail

Usage:
    python facial_recognition_validator.py --image path/to/image.jpg
    python facial_recognition_validator.py --batch path/to/image_folder/
"""

import boto3
import json
import argparse
from pathlib import Path
from datetime import datetime
import csv

rekognition_client = boto3.client('rekognition', region_name='us-east-1')

class FacialRecognitionValidator:
    def __init__(self):
        self.results = []
        self.report_file = f"facial_recognition_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
    def test_image_from_file(self, image_path):
        """Test a single image file with Rekognition"""
        try:
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            response = rekognition_client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )
            
            return self._process_response(response, image_path)
        
        except FileNotFoundError:
            print(f"❌ File not found: {image_path}")
            return None
        except Exception as e:
            print(f"❌ Error processing {image_path}: {str(e)}")
            return None
    
    def _process_response(self, response, image_source):
        """Process Rekognition response and extract relevant metrics"""
        faces_detected = response.get('FaceDetails', [])
        
        if not faces_detected:
            result = {
                'image': image_source,
                'faces_detected': 0,
                'face_count': 0,
                'confidence': 'N/A',
                'age_range': 'N/A',
                'emotions': 'N/A',
                'pose_pitch': 'N/A',
                'pose_roll': 'N/A',
                'pose_yaw': 'N/A',
                'smile': 'N/A',
                'eyes_open': 'N/A',
                'mouth_open': 'N/A',
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            return result
        
        face = faces_detected[0]
        
        result = {
            'image': image_source,
            'faces_detected': len(faces_detected),
            'face_count': 1,
            'confidence': round(face.get('Confidence', 0), 2),
            'age_range': f"{face['AgeRange']['Low']}-{face['AgeRange']['High']}",
            'emotions': self._extract_emotions(face),
            'pose_pitch': round(face['Pose']['Pitch'], 2),
            'pose_roll': round(face['Pose']['Roll'], 2),
            'pose_yaw': round(face['Pose']['Yaw'], 2),
            'smile': face['Smile']['Value'],
            'eyes_open': face['EyesOpen']['Value'],
            'mouth_open': face['MouthOpen']['Value'],
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    def _extract_emotions(self, face):
        """Extract dominant emotion from face data"""
        emotions = face.get('Emotions', [])
        if emotions:
            dominant = max(emotions, key=lambda x: x['Confidence'])
            return f"{dominant['Type']} ({round(dominant['Confidence'], 1)}%)"
        return "N/A"
    
    def print_result(self, result):
        """Pretty print a single result"""
        if result is None:
            return
        
        print("\n" + "="*60)
        print(f"📸 Image: {result['image']}")
        print(f"✓ Faces Detected: {result['faces_detected']}")
        print(f"📊 Detection Confidence: {result['confidence']}%")
        print(f"👤 Age Range: {result['age_range']}")
        print(f"😊 Emotion: {result['emotions']}")
        print(f"🎯 Pose - Pitch: {result['pose_pitch']}°, Roll: {result['pose_roll']}°, Yaw: {result['pose_yaw']}°")
        if result['faces_detected'] > 0:
            print(f"😊 Smiling: {result['smile']} | Eyes Open: {result['eyes_open']} | Mouth Open: {result['mouth_open']}")
        print("="*60)
    
    def save_report(self):
        """Save results to CSV for analysis"""
        if not self.results:
            print("No results to save.")
            return
        
        keys = self.results[0].keys()
        with open(self.report_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"\n✅ Report saved to: {self.report_file}")
    
    def batch_test(self, folder_path):
        """Test all images in a folder"""
        folder = Path(folder_path)
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
        image_files = [f for f in folder.rglob('*') 
                      if f.suffix.lower() in image_extensions]
        
        if not image_files:
            print(f"No images found in {folder_path}")
            return
        
        print(f"\n🔄 Testing {len(image_files)} images...")
        for image_file in image_files:
            print(f"\n→ Processing: {image_file.name}")
            result = self.test_image_from_file(str(image_file))
            if result:
                self.print_result(result)
        
        self.save_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Facial Recognition Validation Framework - Test AWS Rekognition accuracy'
    )
    parser.add_argument('--image', help='Path to a single image file')
    parser.add_argument('--url', help='URL to an image')
    parser.add_argument('--batch', help='Path to folder with multiple images')
    
    args = parser.parse_args()
    
    validator = FacialRecognitionValidator()
    
    if args.image:
        print("🚀 Testing single image with AWS Rekognition...\n")
        result = validator.test_image_from_file(args.image)
        if result:
            validator.print_result(result)
            validator.save_report()
    
    elif args.batch:
        validator.batch_test(args.batch)
    
    else:
        print("Usage:")
        print("  python facial_recognition_validator.py --image path/to/image.jpg")
        print("  python facial_recognition_validator.py --batch path/to/image_folder/")
        print("\nExample:")
        print("  python facial_recognition_validator.py --image test_faces/diverse_sample.jpg")
        print("  python facial_recognition_validator.py --batch test_faces/")