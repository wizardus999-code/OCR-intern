from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path
import numpy as np
import cv2
from dataclasses import dataclass

@dataclass
class TemplateRegion:
    """Represents a region in a document template"""
    x: float
    y: float
    w: float
    h: float
    name: str
    section: str

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
                            section=section
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
                regions[f"{region.section}.{region.name}"] = roi
                
        return regions
        
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
