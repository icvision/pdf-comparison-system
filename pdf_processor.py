import pdf2image
from PIL import Image
import os

class PDFProcessor:
    def __init__(self, dpi=200):
        """
        dpi - jakość konwersji (200 to dobry balans jakość/rozmiar)
        """
        self.dpi = dpi
    
    def pdf_to_images(self, pdf_path, output_folder=None):
        """
        Konwertuje PDF na obrazy
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Nie znaleziono pliku: {pdf_path}")
        
        # Stwórz folder na obrazy jeśli nie istnieje
        if output_folder is None:
            output_folder = "temp_images"
        
        os.makedirs(output_folder, exist_ok=True)
        
        print(f"📄 Konwertuję PDF: {pdf_path}")
        
        # Konwersja PDF → obrazy
        images = pdf2image.convert_from_path(
            pdf_path, 
            dpi=self.dpi,
            fmt='PNG'
        )
        
        image_paths = []
        
        for i, image in enumerate(images):
            image_path = os.path.join(output_folder, f"page_{i+1}.png")
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
            print(f"✅ Strona {i+1} → {image_path}")
        
        print(f"🎉 Konwersja zakończona! {len(images)} stron")
        return image_paths

# Test modułu
if __name__ == "__main__":
    processor = PDFProcessor()
    print("PDF Processor gotowy do testów!")
    print("Aby przetestować, umieść plik PDF w folderze projektu")