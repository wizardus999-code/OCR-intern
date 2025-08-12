import cv2
import numpy as np

class PreprocessingPipeline:
    def __init__(self):
        self.steps = [
            self.convert_to_grayscale,
            self.denoise,
            self.normalize,
            self.deskew
        ]
        
    def process(self, image):
        """Apply all preprocessing steps to the image"""
        result = image.copy()
        for step in self.steps:
            result = step(result)
        return result
        
    def convert_to_grayscale(self, image):
        """Convert image to grayscale if it's not already"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
        
    def denoise(self, image):
        """Remove noise from the image"""
        return cv2.fastNlMeansDenoising(image)
        
    def normalize(self, image):
        """Normalize the image contrast"""
        return cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        
    def deskew(self, image):
        """Correct image skew using the Hough transform"""
        # Find all points that could be lines
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
        
        if lines is not None:
            # Calculate the angle to rotate
            angles = []
            for rho, theta in lines[0]:
                angle = np.degrees(theta)
                if angle < 45:
                    angles.append(angle)
                elif angle > 135:
                    angles.append(angle - 180)
                    
            if angles:
                median_angle = np.median(angles)
                
                # Rotate the image
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                return rotated
                
        return image  # Return original if no rotation needed
