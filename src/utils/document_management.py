from pathlib import Path
import json
import sqlite3
from typing import Dict, Optional, List
import hashlib
import cv2
import numpy as np
from datetime import datetime

class DocumentCache:
    """Cache system for processed documents"""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "document_cache.db"
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database for document caching"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    hash TEXT PRIMARY KEY,
                    template_type TEXT,
                    process_date TEXT,
                    confidence REAL,
                    results TEXT,
                    processing_time REAL
                )
            """)
            conn.commit()
    
    def get_document_hash(self, image: np.ndarray) -> str:
        """Generate unique hash for document image"""
        return hashlib.sha256(image.tobytes()).hexdigest()
    
    def get_cached_results(self, image: np.ndarray) -> Optional[Dict]:
        """Retrieve cached results for a document"""
        doc_hash = self.get_document_hash(image)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT results FROM documents WHERE hash = ?",
                (doc_hash,)
            )
            result = cursor.fetchone()
            
            if result:
                return json.loads(result[0])
        return None
    
    def cache_results(self, 
                     image: np.ndarray,
                     results: Dict,
                     template_type: str,
                     confidence: float,
                     processing_time: float):
        """Cache processing results for a document"""
        doc_hash = self.get_document_hash(image)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents
                (hash, template_type, process_date, confidence, results, processing_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                doc_hash,
                template_type,
                datetime.now().isoformat(),
                confidence,
                json.dumps(results),
                processing_time
            ))
            conn.commit()
    
    def get_processing_history(self, limit: int = 100) -> List[Dict]:
        """Get processing history ordered by date"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT template_type, process_date, confidence, processing_time
                FROM documents
                ORDER BY process_date DESC
                LIMIT ?
            """, (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'template_type': row[0],
                    'process_date': row[1],
                    'confidence': row[2],
                    'processing_time': row[3]
                })
            
            return history

class TemplateManager:
    """Manager for document templates and configurations"""
    
    def __init__(self, templates_dir: str):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates_file = self.templates_dir / "templates.json"
        self._load_templates()
    
    def _load_templates(self):
        """Load template configurations"""
        if self.templates_file.exists():
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
        else:
            self.templates = self._create_default_templates()
            self._save_templates()
    
    def _create_default_templates(self) -> Dict:
        """Create default template configurations"""
        return {
            'identity_card': {
                'name': 'Carte Nationale d\'Identité',
                'name_ar': 'البطاقة الوطنية للتعريف',
                'roi_regions': [
                    {'name': 'name', 'coords': [0.2, 0.3, 0.8, 0.4]},
                    {'name': 'birth_info', 'coords': [0.2, 0.5, 0.8, 0.6]},
                    {'name': 'address', 'coords': [0.2, 0.7, 0.8, 0.8]}
                ],
                'expected_fields': ['name', 'birth_date', 'address']
            },
            'residence_cert': {
                'name': 'Certificat de Résidence',
                'name_ar': 'شهادة السكنى',
                'roi_regions': [
                    {'name': 'header', 'coords': [0.1, 0.1, 0.9, 0.2]},
                    {'name': 'body', 'coords': [0.1, 0.3, 0.9, 0.7]},
                    {'name': 'signature', 'coords': [0.6, 0.8, 0.9, 0.9]}
                ],
                'expected_fields': ['full_name', 'address', 'issue_date']
            },
            # Add more templates as needed
        }
    
    def _save_templates(self):
        """Save template configurations"""
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)
    
    def get_template(self, template_type: str) -> Optional[Dict]:
        """Get template configuration by type"""
        return self.templates.get(template_type)
    
    def add_template(self, template_type: str, config: Dict):
        """Add new template configuration"""
        self.templates[template_type] = config
        self._save_templates()
    
    def update_template(self, template_type: str, config: Dict):
        """Update existing template configuration"""
        if template_type in self.templates:
            self.templates[template_type].update(config)
            self._save_templates()
    
    def get_template_list(self) -> List[Dict]:
        """Get list of available templates"""
        return [
            {
                'type': t_type,
                'name': config['name'],
                'name_ar': config['name_ar']
            }
            for t_type, config in self.templates.items()
        ]
