import cv2
import numpy as np
from PIL import Image
import os

class VisualComparator:
    def __init__(self, threshold=30):
        """
        threshold - próg różnicy pikseli (0-255)
        """
        self.threshold = threshold
    
    def compare_images(self, img1_path, img2_path):
        """
        Porównuje dwa obrazy wizualnie
        """
        # Wczytaj obrazy
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        if img1 is None or img2 is None:
            raise ValueError("Nie można wczytać obrazów")
        
        # Dopasuj rozmiary (jeśli różne)
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        if (h1, w1) != (h2, w2):
            # Resize do mniejszego rozmiaru
            target_h, target_w = min(h1, h2), min(w1, w2)
            img1 = cv2.resize(img1, (target_w, target_h))
            img2 = cv2.resize(img2, (target_w, target_h))
        
        # Oblicz różnicę
        diff = cv2.absdiff(img1, img2)
        
        # Konwertuj do grayscale dla analizy
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Znajdź piksele z różnicami
        _, thresh = cv2.threshold(gray_diff, self.threshold, 255, cv2.THRESH_BINARY)
        
        # Oblicz metryki
        total_pixels = thresh.shape[0] * thresh.shape[1]
        different_pixels = cv2.countNonZero(thresh)
        similarity = 1.0 - (different_pixels / total_pixels)
        
        return {
            'similarity': similarity,
            'different_pixels': different_pixels,
            'total_pixels': total_pixels,
            'diff_image': diff,
            'threshold_image': thresh
        }
    
    def create_highlighted_diff(self, img1_path, img2_path, output_path):
        """
        Tworzy obraz z podświetlonymi różnicami
        """
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        # Dopasuj rozmiary
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        if (h1, w1) != (h2, w2):
            target_h, target_w = min(h1, h2), min(w1, w2)
            img1 = cv2.resize(img1, (target_w, target_h))
            img2 = cv2.resize(img2, (target_w, target_h))
        
        # Oblicz różnicę
        diff = cv2.absdiff(img1, img2)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray_diff, self.threshold, 255, cv2.THRESH_BINARY)
        
        # Stwórz obraz z podświetlonymi różnicami
        highlighted = img1.copy()
        highlighted[thresh > 0] = [0, 0, 255]  # Czerwone podświetlenie
        
        # Zapisz
        cv2.imwrite(output_path, highlighted)
        return output_path

# Test modułu
if __name__ == "__main__":
    comparator = VisualComparator()
    print("Visual Comparator gotowy!")