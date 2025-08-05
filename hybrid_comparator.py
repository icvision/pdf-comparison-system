from pdf_processor import PDFProcessor
from text_extractor import TextExtractor
from visual_comparator import VisualComparator
import difflib
from dataclasses import dataclass
from typing import List, Dict
import os

@dataclass
class HybridComparisonResult:
    """Rozszerzona struktura wyników - OCR + Vision"""
    page_number: int
    # OCR results
    text_differences: List[str]
    text_similarity_score: float
    has_text_differences: bool
    # Visual results
    visual_similarity_score: float
    different_pixels: int
    total_pixels: int
    has_visual_differences: bool
    # Combined
    overall_similarity: float
    highlighted_diff_path: str = None

class HybridComparator:
    def __init__(self):
        self.processor = PDFProcessor(dpi=200)
        self.extractor = TextExtractor()
        self.visual_comparator = VisualComparator(threshold=30)
    
    def compare_pdfs_hybrid(self, pdf1_path: str, pdf2_path: str):
        """
        Hybrydowe porównanie: OCR + Computer Vision
        """
        print("🔍 Rozpoczynam hybrydowe porównanie PDF-ów...")
        
        # Krok 1: Konwertuj oba PDF-y
        print("\n📄 Konwertuję pierwszy PDF...")
        images1 = self.processor.pdf_to_images(pdf1_path, "temp_pdf1")
        
        print("\n📄 Konwertuję drugi PDF...")
        images2 = self.processor.pdf_to_images(pdf2_path, "temp_pdf2")
        
        # Sprawdź czy mają tyle samo stron
        if len(images1) != len(images2):
            print(f"⚠️ Różna liczba stron: PDF1={len(images1)}, PDF2={len(images2)}")
        
        # Krok 2: Analiza OCR
        print("\n🔍 Analiza tekstowa (OCR)...")
        text1 = self.extractor.extract_text_from_pdf_images(images1)
        text2 = self.extractor.extract_text_from_pdf_images(images2)
        
        # Krok 3: Analiza wizualna + hybrydowe porównanie
        results = []
        max_pages = max(len(images1), len(images2))
        
        # Stwórz folder na highlighted różnice
        os.makedirs("highlighted_diffs", exist_ok=True)
        
        for i in range(max_pages):
            page_num = i + 1
            print(f"\n📊 Analizuję stronę {page_num} (OCR + Vision)...")
            
            # Pobierz ścieżki obrazów
            img1_path = images1[i] if i < len(images1) else None
            img2_path = images2[i] if i < len(images2) else None
            
            if img1_path and img2_path:
                result = self._compare_page_hybrid(
                    page_num, 
                    text1.get(f"page_{page_num}", ""),
                    text2.get(f"page_{page_num}", ""),
                    img1_path,
                    img2_path
                )
                results.append(result)
        
        return results
    
    def _compare_page_hybrid(self, page_num: int, text1: str, text2: str, 
                           img1_path: str, img2_path: str) -> HybridComparisonResult:
        """
        Hybrydowe porównanie pojedynczej strony
        """
        # === ANALIZA TEKSTOWA (OCR) ===
        text_similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        differ = difflib.unified_diff(
            text1.splitlines(keepends=True),
            text2.splitlines(keepends=True),
            fromfile=f'PDF1_page_{page_num}',
            tofile=f'PDF2_page_{page_num}',
            lineterm=''
        )
        
        text_differences = list(differ)
        has_text_differences = len(text_differences) > 0
        
        # === ANALIZA WIZUALNA (Computer Vision) ===
        visual_result = self.visual_comparator.compare_images(img1_path, img2_path)
        visual_similarity = visual_result['similarity']
        different_pixels = visual_result['different_pixels']
        total_pixels = visual_result['total_pixels']
        has_visual_differences = different_pixels > 0
        
        # Stwórz highlighted diff
        highlighted_path = f"highlighted_diffs/page_{page_num}_diff.png"
        self.visual_comparator.create_highlighted_diff(img1_path, img2_path, highlighted_path)
        
        # === KOMBINACJA WYNIKÓW ===
        # Średnia ważona: 60% vision, 40% OCR (vision jest bardziej precyzyjne)
        overall_similarity = (visual_similarity * 0.6) + (text_similarity * 0.4)
        
        print(f"   📝 Podobieństwo tekstowe: {text_similarity:.2%}")
        print(f"   👁️ Podobieństwo wizualne: {visual_similarity:.2%}")
        print(f"   🎯 Podobieństwo ogólne: {overall_similarity:.2%}")
        
        return HybridComparisonResult(
            page_number=page_num,
            # OCR
            text_differences=text_differences,
            text_similarity_score=text_similarity,
            has_text_differences=has_text_differences,
            # Vision
            visual_similarity_score=visual_similarity,
            different_pixels=different_pixels,
            total_pixels=total_pixels,
            has_visual_differences=has_visual_differences,
            # Combined
            overall_similarity=overall_similarity,
            highlighted_diff_path=highlighted_path
        )

# Test modułu
if __name__ == "__main__":
    comparator = HybridComparator()
    print("Hybrid Comparator gotowy!")