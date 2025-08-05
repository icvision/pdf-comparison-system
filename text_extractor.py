import pytesseract
from PIL import Image
import os

class TextExtractor:
    def __init__(self):
        # Ustaw ścieżkę do Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def extract_text_from_image(self, image_path):
        """
        Wyciąga tekst z pojedynczego obrazu
        """
        try:
            image = Image.open(image_path)
            # Konfiguracja OCR - lepsze wyniki dla dokumentów
            config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, config=config, lang='eng+pol')
            return text.strip()
        except Exception as e:
            print(f"❌ Błąd OCR dla {image_path}: {e}")
            return ""
    
    def extract_text_from_pdf_images(self, image_paths):
        """
        Wyciąga tekst ze wszystkich obrazów PDF
        """
        all_text = {}
        
        for i, image_path in enumerate(image_paths):
            print(f"🔍 Analizuję stronę {i+1}...")
            text = self.extract_text_from_image(image_path)
            all_text[f"page_{i+1}"] = text
            print(f"✅ Strona {i+1}: {len(text)} znaków")
        
        return all_text

# Test modułu
if __name__ == "__main__":
    extractor = TextExtractor()
    print("Text Extractor gotowy!")