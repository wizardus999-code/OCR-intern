from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path
import numpy as np
import cv2
from dataclasses import dataclass

from src.postprocessing.validators import normalize_field

@dataclass
class TemplateRegion:
    """Represents a region in a document template with OCR configuration"""
    x: float
    y: float
    w: float
    h: float
    name: str
    section: str
    lang: Optional[str] = None
    psm: Optional[int] = None
    oem: Optional[int] = None
    dpi: Optional[int] = None
    scale: Optional[float] = None
    whitelist: Optional[str] = None
    preserve_spaces: Optional[bool] = None

@dataclass
class Template:
    """Represents a document template with its regions"""
    name: str
    name_ar: str
    version: str
    regions: List[TemplateRegion]
    required_fields: List[str]

class TemplateExtractor:
    """Class for extracting information from documents based on templates"""
    
    def __init__(self, templates_path: str):
        self.templates: Dict[str, Template] = {}
        self._load_templates(templates_path)
        
    def _load_templates(self, templates_path: str):
        """Load templates from JSON file"""
        try:
            with open(templates_path, 'r', encoding='utf-8') as f:
                raw_templates = json.load(f)
                
            for template_id, template_data in raw_templates.items():
                regions = []
                # Process each section of regions
                for section, section_data in template_data['regions'].items():
                    for region_name, region_coords in section_data.items():
                        regions.append(TemplateRegion(
                            x=region_coords['x'],
                            y=region_coords['y'],
                            w=region_coords['w'],
                            h=region_coords['h'],
                            name=region_name,
                            section=section,
                            lang=region_coords.get('lang'),
                            psm=region_coords.get('psm'),
                            oem=region_coords.get('oem'),
                            dpi=region_coords.get('dpi'),
                            scale=region_coords.get('scale'),
                            whitelist=region_coords.get('whitelist'),
                            preserve_spaces=region_coords.get('preserve_spaces')
                        ))
                
                self.templates[template_id] = Template(
                    name=template_data['name'],
                    name_ar=template_data['name_ar'],
                    version=template_data['template_version'],
                    regions=regions,
                    required_fields=template_data['required_fields']
                )
                
        except Exception as e:
            raise RuntimeError(f"Failed to load templates: {str(e)}")
            
    def extract_regions(self, 
                       image: np.ndarray, 
                       template_id: str) -> Dict[str, np.ndarray]:
        """Extract regions from document according to template"""
        if template_id not in self.templates:
            raise ValueError(f"Unknown template: {template_id}")
            
        template = self.templates[template_id]
        h, w = image.shape[:2]
        regions = {}
        
        for region in template.regions:
            # Convert relative coordinates to absolute
            x1 = int(region.x * w)
            y1 = int(region.y * h)
            x2 = int((region.x + region.w) * w)
            y2 = int((region.y + region.h) * h)
            
            # Extract region from image
            roi = image[y1:y2, x1:x2]
            if roi.size > 0:
                regions[f"{region.section}.{region.name}"] = {
                    'image': roi,
                    'bbox': [x1, y1, x2-x1, y2-y1],
                    'lang': region.lang
                }
                
        return regions
        
    def process_regions(self,
                       image: np.ndarray,
                       template_id: str,
                       ocr_engine) -> Dict[str, Any]:
        """Process regions using OCR and validation"""
        regions = self.extract_regions(image, template_id)
        out = {'fields': {}, 'raw': {}}
        
        for field_id, region_info in regions.items():
            section, name = field_id.split('.')
            roi = region_info['image']
            lang = region_info['lang']
            bbox = region_info['bbox']
            
            # Build OCR configuration
            config = {}
            region = next(r for r in self.templates[template_id].regions 
                        if r.section == section and r.name == name)
            
            if region.psm is not None:
                config['psm'] = region.psm
            if region.oem is not None:
                config['oem'] = region.oem
            if region.dpi is not None:
                config['dpi'] = region.dpi
            if region.whitelist is not None:
                config['whitelist'] = region.whitelist
            if region.preserve_spaces is not None:
                config['preserve_interword_spaces'] = region.preserve_spaces
            if region.scale is not None and region.scale != 1.0:
                h, w = roi.shape[:2]
                new_h, new_w = int(h * region.scale), int(w * region.scale)
                roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

            # Process with appropriate language and config
            results = ocr_engine.process_document(roi, **config)
            
            # Find best result by confidence
            best_text = ""
            best_conf = -1
            lang_key = 'ara' if region.lang == 'arabic' else 'fra'
            
            if lang_key in results:
                for result in results[lang_key]:
                    if result.confidence > best_conf:
                        best_text = result.text
                        best_conf = result.confidence
            
            # Apply normalization and validation
            norm = normalize_field(f"{section}.{name}", best_text)
            out['fields'][f"{section}.{name}"] = {
                'value': best_text,
                'norm': norm.get('value'),
                'valid': bool(norm.get('valid')),
                'type': norm.get('type'),
                'conf': best_conf,
                'lang': lang_key,
                'bbox': bbox,
            }
            out['raw'].setdefault(lang_key, []).extend(results.get(lang_key, []))
            
        return out
        
    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific template"""
        if template_id not in self.templates:
            return None
            
        template = self.templates[template_id]
        return {
            'name': template.name,
            'name_ar': template.name_ar,
            'version': template.version,
            'required_fields': template.required_fields,
            'regions_count': len(template.regions)
        }
        
    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates"""
        return [
            {
                'id': template_id,
                'name': template.name,
                'name_ar': template.name_ar,
                'version': template.version
            }
            for template_id, template in self.templates.items()
        ]
        
    @staticmethod
    def preprocess_region(region: np.ndarray) -> np.ndarray:
        """Preprocess a region for optimal OCR"""
        if len(region.shape) == 3:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        else:
            gray = region.copy()
            
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced)
        
        # Threshold
        _, binary = cv2.threshold(
            denoised, 0, 255, 
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        return binary
