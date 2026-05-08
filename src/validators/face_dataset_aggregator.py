"""
Diverse Face Dataset Aggregator
Automatically downloads diverse face images from Unsplash
Validates each image contains a face using AWS Rekognition
Organizes into structured dataset for accessibility testing

Usage:
    python face_dataset_aggregator.py --count 50 --output test_faces/
    python face_dataset_aggregator.py --count 100 --diverse
"""

import os
import csv
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime
import boto3

UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
UNSPLASH_ACCESS_KEY = "ROnh9ojHDNGReZ-6gefBBkXfcEA5a_e4B7zo8ruBqF0"

rekognition_client = boto3.client('rekognition', region_name='us-east-1')

class FaceDatasetAggregator:
    def __init__(self, output_dir="test_faces"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.categories = {
            'skin_tone_diverse': self.output_dir / 'skin_tone_diverse',
            'age_ranges': self.output_dir / 'age_ranges',
            'lighting_conditions': self.output_dir / 'lighting_conditions',
            'poses_and_angles': self.output_dir / 'poses_and_angles',
            'accessibility_scenarios': self.output_dir / 'accessibility_scenarios',
            'validated': self.output_dir / 'validated'
        }
        
        for category_path in self.categories.values():
            category_path.mkdir(exist_ok=True)
        
        self.metadata = []
        self.metadata_file = self.output_dir / f"dataset_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    def search_unsplash(self, query, page=1, per_page=20):
        """Search Unsplash for images matching query"""
        params = {
            'query': query,
            'page': page,
            'per_page': per_page,
            'client_id': UNSPLASH_ACCESS_KEY
        }
        
        try:
            response = requests.get(UNSPLASH_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"Error searching Unsplash: {str(e)}")
            return []
    
    def download_image(self, url, filename):
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            return False
    
    def validate_face(self, image_path):
        """Use Rekognition to validate image contains a face"""
        try:
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            response = rekognition_client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )
            
            faces = response.get('FaceDetails', [])
            
            if not faces:
                return None, "No face detected"
            
            face = faces[0]
            face_data = {
                'faces_detected': len(faces),
                'confidence': round(face.get('Confidence', 0), 2),
                'age_range': f"{face['AgeRange']['Low']}-{face['AgeRange']['High']}",
                'pitch': round(face['Pose']['Pitch'], 2),
                'roll': round(face['Pose']['Roll'], 2),
                'yaw': round(face['Pose']['Yaw'], 2),
                'smile': face['Smile']['Value'],
                'eyes_open': face['EyesOpen']['Value'],
                'mouth_open': face['MouthOpen']['Value'],
                'quality_brightness': round(face['Quality']['Brightness'], 2),
                'quality_sharpness': round(face['Quality']['Sharpness'], 2)
            }
            
            return face_data, "Valid"
        
        except Exception as e:
            return None, f"Validation error: {str(e)}"
    
    def categorize_image(self, image_path, face_data):
        """Determine which category folder to save image to"""
        category = 'validated'
        
        if face_data:
            age_low = int(face_data['age_range'].split('-')[0])
            if age_low < 25:
                category = 'age_ranges'
            elif face_data['yaw'] > 30 or face_data['yaw'] < -30:
                category = 'poses_and_angles'
            elif face_data['quality_brightness'] < 50:
                category = 'lighting_conditions'
        
        return self.categories[category]
    
    def aggregate_dataset(self, search_queries, target_count=50):
        """Main function to aggregate diverse faces"""
        downloaded = 0
        validated = 0
        failed = 0
        
        print(f"\n🔄 Starting dataset aggregation...")
        print(f"Target: {target_count} validated faces")
        print(f"Searches: {', '.join(search_queries)}\n")
        
        for query in search_queries:
            if validated >= target_count:
                break
            
            print(f"🔍 Searching: '{query}'")
            results = self.search_unsplash(query, per_page=20)
            
            if not results:
                print(f"   No results found for '{query}'")
                continue
            
            for result in results:
                if validated >= target_count:
                    break
                
                image_url = result.get('urls', {}).get('regular')
                if not image_url:
                    continue
                
                filename = f"{result.get('id', 'unknown')}.jpg"
                image_path = self.output_dir / filename
                
                print(f"   Downloading: {filename}...", end=" ")
                if not self.download_image(image_url, image_path):
                    failed += 1
                    continue
                
                downloaded += 1
                
                face_data, status = self.validate_face(image_path)
                
                if face_data:
                    validated += 1
                    
                    category_dir = self.categorize_image(image_path, face_data)
                    new_path = category_dir / filename
                    image_path.rename(new_path)
                    
                    metadata_entry = {
                        'filename': filename,
                        'category': category_dir.name,
                        'source': 'unsplash',
                        'source_url': result.get('links', {}).get('html', ''),
                        'photographer': result.get('user', {}).get('name', 'Unknown'),
                        'faces_detected': face_data.get('faces_detected'),
                        'confidence': face_data.get('confidence'),
                        'age_range': face_data.get('age_range'),
                        'pitch': face_data.get('pitch'),
                        'roll': face_data.get('roll'),
                        'yaw': face_data.get('yaw'),
                        'smile': face_data.get('smile'),
                        'eyes_open': face_data.get('eyes_open'),
                        'brightness': face_data.get('quality_brightness'),
                        'sharpness': face_data.get('quality_sharpness'),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.metadata.append(metadata_entry)
                    
                    print(f"OK (Confidence: {face_data['confidence']}%)")
                else:
                    print(f"{status}")
                    failed += 1
        
        self.save_metadata()
        
        print(f"\n" + "="*60)
        print(f"DATASET AGGREGATION COMPLETE")
        print(f"="*60)
        print(f"Downloaded: {downloaded}")
        print(f"Validated: {validated}")
        print(f"Failed: {failed}")
        print(f"Success rate: {round(100*validated/max(downloaded, 1), 1)}%")
        print(f"\nDataset location: {self.output_dir}")
        print(f"Metadata file: {self.metadata_file}")
        print(f"="*60)
    
    def save_metadata(self):
        """Save metadata to CSV"""
        if not self.metadata:
            print("No metadata to save.")
            return
        
        keys = self.metadata[0].keys()
        with open(self.metadata_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.metadata)
        
        print(f"\nMetadata saved to: {self.metadata_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Diverse Face Dataset Aggregator'
    )
    parser.add_argument('--count', type=int, default=50, 
                       help='Target number of validated faces (default: 50)')
    parser.add_argument('--output', default='test_faces', 
                       help='Output directory for dataset (default: test_faces)')
    parser.add_argument('--diverse', action='store_true',
                       help='Use diverse search queries (recommended)')
    
    args = parser.parse_args()
    
    if args.diverse:
        queries = [
            'diverse faces',
            'headshot portrait',
            'people different ethnicities',
            'profile face angle',
            'woman portrait',
            'man portrait',
            'older adults',
            'young people',
            'glasses',
            'smile face'
        ]
    else:
        queries = ['faces', 'portrait', 'headshot']
    
    aggregator = FaceDatasetAggregator(output_dir=args.output)
    aggregator.aggregate_dataset(queries, target_count=args.count)
