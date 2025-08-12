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
            text = result['text']
            confidence = result['confidence']
            
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
        text_lower = text.lower()
        
        # Check for common document indicators
        if any(prefix in text_lower for prefix in self.morocco_prefixes):
            if 'certificat' in text_lower or 'شهادة' in text:
                return 'certificate'
            elif 'demande' in text_lower or 'طلب' in text:
                return 'application'
            elif 'déclaration' in text_lower or 'تصريح' in text:
                return 'declaration'
                
        return None
