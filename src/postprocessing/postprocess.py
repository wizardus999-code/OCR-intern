from langdetect import detect
import re

class PostProcessor:
    def __init__(self):
        # Common prefixes in Moroccan administrative documents
        self.morocco_prefixes = [
            'royaume du maroc',
            'المملكة المغربية',
            'ministère',
            'وزارة',
            'préfecture',
            'عمالة'
        ]
        
    def process(self, text_results):
        """Process OCR results to improve accuracy and extract metadata"""
        processed_results = {
            'text': [],
            'metadata': {
                'document_type': None,
                'languages_detected': set(),
                'confidence': 0.0
            }
        }
        
        total_confidence = 0
        texts = []
        
        # Process each text block
        for result in text_results:
            if isinstance(result, dict):
                text = result.get('text', '')
                confidence = result.get('confidence', 0)
            else:
                text = str(result)
                confidence = 0
            
            # Clean the text
            cleaned_text = self._clean_text(text)
            if cleaned_text:
                texts.append(cleaned_text)
                total_confidence += confidence
                
                # Detect language
                try:
                    lang = detect(cleaned_text)
                    processed_results['metadata']['languages_detected'].add(lang)
                except:
                    pass
                
                # Check for document type indicators
                doc_type = self._detect_document_type(cleaned_text)
                if doc_type and not processed_results['metadata']['document_type']:
                    processed_results['metadata']['document_type'] = doc_type
        
        # Calculate average confidence
        if texts:
            processed_results['metadata']['confidence'] = total_confidence / len(texts)
        
        processed_results['text'] = texts
        return processed_results
    
    def _clean_text(self, text):
        """Clean and normalize text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep Arabic and French characters
        text = re.sub(r'[^\w\s\u0600-\u06FF.,()-]', '', text)
        
        return text.strip()
    
    def _detect_document_type(self, text):
        """Attempt to determine document type based on content"""
        text_lower = text.lower().strip()
        
        # Normalized dictionary for document types with keywords and patterns
        doc_types = {
            'certificate': {
                'fr': ['certificat', 'attestation', 'acte'],
                'ar': ['شهادة', 'وثيقة'],
                'patterns': [
                    r'certificat\s+(de|du|des)\s+\w+',
                    r'attestation\s+(de|du|des)\s+\w+',
                    r'شهادة\s+[\u0600-\u06FF\s]+',
                ],
                'weight': 1.0
            },
            'application': {
                'fr': ['demande', 'formulaire', 'requête'],
                'ar': ['طلب', 'استمارة'],
                'patterns': [
                    r'demande\s+(de|du|des)\s+\w+',
                    r'طلب\s+[\u0600-\u06FF\s]+',
                ],
                'weight': 0.9
            },
            'declaration': {
                'fr': ['déclaration', 'declaration'],
                'ar': ['تصريح', 'إقرار', 'إعلان'],
                'patterns': [
                    r'd[ée]claration\s+(de|du|des)\s+\w+',
                    r'تصريح\s+[\u0600-\u06FF\s]+',
                ],
                'weight': 0.8
            }
        }
        
        # Score accumulator for each document type
        scores = {doc_type: 0.0 for doc_type in doc_types.keys()}
        
        # Process the text
        words = text_lower.split()
        text_ar = ''.join(char for char in text_lower if '\u0600' <= char <= '\u06FF')
        
        for doc_type, type_data in doc_types.items():
            # Check French keywords
            for keyword in type_data['fr']:
                if keyword in text_lower:
                    scores[doc_type] += 1.0 * type_data['weight']
            
            # Check Arabic keywords
            for keyword in type_data['ar']:
                if keyword in text_ar:
                    scores[doc_type] += 1.0 * type_data['weight']
            
            # Check patterns
            for pattern in type_data['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    scores[doc_type] += 2.0 * type_data['weight']
                    
            # Boost score if document has clear headers/footers
            if any(prefix in text_lower for prefix in self.morocco_prefixes):
                scores[doc_type] *= 1.2
        
        # Get document type with highest score
        best_type = max(scores.items(), key=lambda x: x[1])
        
        # Only return if we have a clear signal
        if best_type[1] > 0.5:
            return best_type[0]
                
        return None
