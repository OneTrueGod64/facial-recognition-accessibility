"""
Multi-System Facial Recognition Validator
Tests AWS Rekognition, Google Vision API, and Azure Face API
Compares results across platforms for accessibility research

Usage:
    python multi_system_validator.py --image path/to/image.jpg --systems aws google azure
    python multi_system_validator.py --batch path/to/folder/ --systems all
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import csv
from typing import Dict, List, Optional
import sys

# AWS
try:
    import boto3
except ImportError:
    boto3 = None

# Google Cloud
try:
    from google.cloud import vision
    from google.oauth2 import service_account
except ImportError:
    vision = None

# Azure
try:
    import requests
except ImportError:
    requests = None


class MultiSystemValidator:
    def __init__(self, config_file='config.json'):
        self.config = self._load_config(config_file)
        self.results = []
        self.report_file = f"multi_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Initialize clients
        self.aws_client = self._init_aws()
        self.google_client = self._init_google()
        self.azure_client = self._init_azure()
        
    def _load_config(self, config_file):
        """Load credentials from config file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file not found: {config_file}")
            print("   Create config.json with your API credentials")
            return {}
    
    def _init_aws(self):
        """Initialize AWS Rekognition client"""
        try:
            return boto3.client('rekognition', region_name='us-east-1')
        except Exception as e:
            print(f"⚠️  AWS not available: {str(e)}")
            return None
    
    def _init_google(self):
        """Initialize Google Vision client"""
        try:
            if 'google_service_account_path' in self.config:
                credentials = service_account.Credentials.from_service_account_file(
                    self.config['google_service_account_path']
                )
                return vision.ImageAnnotatorClient(credentials=credentials)
            return None
        except Exception as e:
            print(f"⚠️  Google Vision not available: {str(e)}")
            return None
    
    def _init_azure(self):
        """Initialize Azure Face API client"""
        try:
            if 'azure_endpoint' in self.config and 'azure_key' in self.config:
                return {
                    'endpoint': self.config['azure_endpoint'],
                    'key': self.config['azure_key']
                }
            return None
        except Exception as e:
            print(f"⚠️  Azure not available: {str(e)}")
            return None
    
    def test_image(self, image_path, systems=['aws', 'google', 'azure']):
        """Test single image across multiple systems"""
        systems = [s.lower() for s in systems]
        
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
        except FileNotFoundError:
            print(f"❌ File not found: {image_path}")
            return None
        
        result = {
            'image': str(image_path),
            'timestamp': datetime.now().isoformat(),
            'file_size_bytes': len(image_bytes)
        }
        
        # Test AWS
        if 'aws' in systems and self.aws_client:
            aws_result = self._test_aws(image_bytes)
            result['aws'] = aws_result
        
        # Test Google
        if 'google' in systems and self.google_client:
            google_result = self._test_google(image_bytes)
            result['google'] = google_result
        
        # Test Azure
        if 'azure' in systems and self.azure_client:
            azure_result = self._test_azure(image_bytes)
            result['azure'] = azure_result
        
        self.results.append(result)
        return result
    
    def _test_aws(self, image_bytes) -> Dict:
        """Test image with AWS Rekognition"""
        try:
            response = self.aws_client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )
            
            faces = response.get('FaceDetails', [])
            if not faces:
                return {'status': 'no_faces', 'face_count': 0}
            
            face = faces[0]
            return {
                'status': 'success',
                'face_count': len(faces),
                'confidence': round(face.get('Confidence', 0), 2),
                'age_low': face['AgeRange']['Low'],
                'age_high': face['AgeRange']['High'],
                'emotion': max(face.get('Emotions', []), key=lambda x: x['Confidence'])['Type'],
                'emotion_confidence': round(max(face.get('Emotions', []), key=lambda x: x['Confidence'])['Confidence'], 2),
                'smile': face['Smile']['Value'],
                'eyes_open': face['EyesOpen']['Value'],
                'mouth_open': face['MouthOpen']['Value'],
                'pose_pitch': round(face['Pose']['Pitch'], 2),
                'pose_roll': round(face['Pose']['Roll'], 2),
                'pose_yaw': round(face['Pose']['Yaw'], 2)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _test_google(self, image_bytes) -> Dict:
        """Test image with Google Vision API"""
        try:
            from google.cloud.vision import types
            
            image = vision.Image(content=image_bytes)
            response = self.google_client.face_detection(image=image)
            
            faces = response.face_annotations
            if not faces:
                return {'status': 'no_faces', 'face_count': 0}
            
            face = faces[0]
            
            # Map Google emotions to readable names
            emotions = {
                'JOY': 'HAPPY',
                'SORROW': 'SAD',
                'ANGER': 'ANGRY',
                'SURPRISE': 'SURPRISED',
                'CONFIDENCE': 'CALM',
                'HEADWEAR': 'HEADWEAR'
            }
            
            likelihood_map = {0: 'UNKNOWN', 1: 'VERY_UNLIKELY', 2: 'UNLIKELY', 3: 'POSSIBLE', 4: 'LIKELY', 5: 'VERY_LIKELY'}
            
            return {
                'status': 'success',
                'face_count': len(faces),
                'confidence': round(face.detection_confidence * 100, 2),
                'joy_likelihood': likelihood_map.get(face.joy_likelihood, 'UNKNOWN'),
                'sorrow_likelihood': likelihood_map.get(face.sorrow_likelihood, 'UNKNOWN'),
                'anger_likelihood': likelihood_map.get(face.anger_likelihood, 'UNKNOWN'),
                'surprise_likelihood': likelihood_map.get(face.surprise_likelihood, 'UNKNOWN'),
                'eyes_open_likelihood': likelihood_map.get(face.eyes_open_likelihood, 'UNKNOWN'),
                'mouth_open_likelihood': likelihood_map.get(face.mouth_open_likelihood, 'UNKNOWN'),
                'pose_pan': round(face.pan_angle, 2),
                'pose_tilt': round(face.tilt_angle, 2),
                'pose_roll': round(face.roll_angle, 2)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _test_azure(self, image_bytes) -> Dict:
        """Test image with Azure Face API"""
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.azure_client['key'],
                'Content-Type': 'application/octet-stream'
            }
            
            params = {
                'returnFaceId': 'true',
                'returnFaceAttributes': 'age,emotion,facialHair,headPose,smile,eyesOpen,mouthOpen'
            }
            
            response = requests.post(
                f"{self.azure_client['endpoint']}/face/v1.0/detect",
                headers=headers,
                params=params,
                data=image_bytes
            )
            
            if response.status_code != 200:
                return {'status': 'error', 'error': f"API error: {response.status_code}"}
            
            faces = response.json()
            if not faces:
                return {'status': 'no_faces', 'face_count': 0}
            
            face = faces[0]
            attributes = face.get('faceAttributes', {})
            
            # Get dominant emotion
            emotions = attributes.get('emotion', {})
            dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0].upper() if emotions else 'UNKNOWN'
            
            return {
                'status': 'success',
                'face_count': len(faces),
                'confidence': round(face.get('faceRectangle', {}).get('width', 0) / 100, 2),  # Approximate
                'age': attributes.get('age'),
                'emotion': dominant_emotion,
                'smile': attributes.get('smile', 0),
                'eyes_open': attributes.get('eyesOpen', 0),
                'mouth_open': attributes.get('mouthOpen', 0),
                'head_pose_pitch': round(attributes.get('headPose', {}).get('pitch', 0), 2),
                'head_pose_roll': round(attributes.get('headPose', {}).get('roll', 0), 2),
                'head_pose_yaw': round(attributes.get('headPose', {}).get('yaw', 0), 2)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def print_comparison(self, result):
        """Pretty print comparison results"""
        print("\n" + "="*80)
        print(f"📸 Image: {result['image']}")
        print("="*80)
        
        for system in ['aws', 'google', 'azure']:
            if system in result:
                data = result[system]
                print(f"\n{system.upper():^20}")
                print("-"*40)
                
                if data.get('status') == 'no_faces':
                    print(f"  ❌ No faces detected")
                elif data.get('status') == 'error':
                    print(f"  ⚠️  Error: {data.get('error')}")
                else:
                    print(f"  ✓ Faces detected: {data.get('face_count')}")
                    print(f"  Confidence: {data.get('confidence', 'N/A')}%")
                    
                    if 'age_low' in data:
                        print(f"  Age: {data['age_low']}-{data['age_high']}")
                    elif 'age' in data:
                        print(f"  Age: {data['age']}")
                    
                    if 'emotion' in data:
                        print(f"  Emotion: {data.get('emotion')}")
                    
                    if 'pose_yaw' in data:
                        print(f"  Pose (Y/P/R): {data['pose_yaw']}°/{data.get('pose_pitch', 'N/A')}°/{data.get('pose_roll', 'N/A')}°")
                    elif 'pose_pan' in data:
                        print(f"  Pose (Pan/Tilt/Roll): {data['pose_pan']}°/{data['pose_tilt']}°/{data['pose_roll']}°")
        
        print("\n" + "="*80)
    
    def batch_test(self, folder_path, systems=['aws', 'google', 'azure']):
        """Test all images in folder"""
        folder = Path(folder_path)
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
        image_files = [f for f in folder.rglob('*') 
                      if f.suffix.lower() in image_extensions]
        
        if not image_files:
            print(f"No images found in {folder_path}")
            return
        
        print(f"\n🔄 Testing {len(image_files)} images across {', '.join(systems)}...")
        
        for i, image_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Processing: {image_file.name}")
            result = self.test_image(str(image_file), systems)
            if result:
                self.print_comparison(result)
        
        self.save_report()
    
    def save_report(self):
        """Save results to CSV for analysis"""
        if not self.results:
            print("No results to save.")
            return
        
        # Flatten results for CSV
        flattened = []
        for result in self.results:
            row = {
                'image': result['image'],
                'timestamp': result['timestamp'],
                'file_size_bytes': result['file_size_bytes']
            }
            
            # Flatten each system's results
            for system in ['aws', 'google', 'azure']:
                if system in result:
                    data = result[system]
                    for key, value in data.items():
                        row[f'{system}_{key}'] = value
            
            flattened.append(row)
        
        # Get all possible keys
        all_keys = set()
        for row in flattened:
            all_keys.update(row.keys())
        
        keys = sorted(all_keys)
        
        with open(self.report_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(flattened)
        
        print(f"\n✅ Report saved to: {self.report_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Multi-system facial recognition validator'
    )
    parser.add_argument('--image', help='Path to single image')
    parser.add_argument('--batch', help='Path to image folder')
    parser.add_argument('--systems', default='aws,google,azure', 
                       help='Systems to test (comma-separated: aws,google,azure)')
    parser.add_argument('--config', default='config.json',
                       help='Path to config.json with API credentials')
    
    args = parser.parse_args()
    
    systems = [s.strip() for s in args.systems.split(',')]
    
    validator = MultiSystemValidator(args.config)
    
    if args.image:
        result = validator.test_image(args.image, systems)
        if result:
            validator.print_comparison(result)
            validator.save_report()
    elif args.batch:
        validator.batch_test(args.batch, systems)
    else:
        print("Usage:")
        print("  python multi_system_validator.py --image path/to/image.jpg")
        print("  python multi_system_validator.py --batch path/to/folder/")
        print("  python multi_system_validator.py --batch path/to/folder/ --systems aws,google")
