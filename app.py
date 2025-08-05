import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os
import zipfile
import io
from pdf2image import convert_from_bytes
import pytesseract
import difflib
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

# Konfiguracja strony
st.set_page_config(
    page_title="PDF Comparison System - Demo",
    page_icon="📄",
    layout="wide"
)

# ===== KLASY I FUNKCJE =====

@dataclass
class HybridComparisonResult:
    """Rozszerzona struktura wyników - OCR + Vision"""
    page_number: int
    text_differences: List[str]
    text_similarity_score: float
    has_text_differences: bool
    visual_similarity_score: float
    different_pixels: int
    total_pixels: int
    has_visual_differences: bool
    overall_similarity: float
    highlighted_diff_path: str = None

class PDFProcessor:
    def __init__(self, dpi=200):
        self.dpi = dpi
    
    def pdf_to_images(self, pdf_bytes, output_folder):
        """Konwertuje PDF na obrazy"""
        os.makedirs(output_folder, exist_ok=True)
        
        try:
            images = convert_from_bytes(pdf_bytes, dpi=self.dpi)
            image_paths = []
            
            for i, image in enumerate(images):
                image_path = os.path.join(output_folder, f"page_{i+1}.png")
                image.save(image_path, 'PNG')
                image_paths.append(image_path)
            
            return image_paths
        except Exception as e:
            st.error(f"Błąd konwersji PDF: {e}")
            return []

class TextExtractor:
    def __init__(self):
        self.config = '--oem 3 --psm 6'
    
    def extract_text_from_pdf_images(self, image_paths):
        """Wyciąga tekst z obrazów PDF"""
        extracted_text = {}
        
        for i, image_path in enumerate(image_paths):
            try:
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image, config=self.config, lang='pol+nld+eng')
                extracted_text[f"page_{i+1}"] = text.strip()
            except Exception as e:
                st.error(f"Błąd OCR na stronie {i+1}: {e}")
                extracted_text[f"page_{i+1}"] = ""
        
        return extracted_text

class VisualComparator:
    def __init__(self, threshold=30):
        self.threshold = threshold
    
    def compare_images(self, img1_path, img2_path):
        """Porównuje dwa obrazy wizualnie"""
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        
        if img1 is None or img2 is None:
            raise ValueError("Nie można wczytać obrazów")
        
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
        """Tworzy obraz z podświetlonymi różnicami"""
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

class HybridComparator:
    def __init__(self):
        self.processor = PDFProcessor(dpi=200)
        self.extractor = TextExtractor()
        self.visual_comparator = VisualComparator(threshold=30)
    
    def compare_pdfs_hybrid(self, pdf1_bytes, pdf2_bytes):
        """Hybrydowe porównanie: OCR + Computer Vision"""
        
        # Konwertuj oba PDF-y
        images1 = self.processor.pdf_to_images(pdf1_bytes, "temp_pdf1")
        images2 = self.processor.pdf_to_images(pdf2_bytes, "temp_pdf2")
        
        if not images1 or not images2:
            return []
        
        # Analiza OCR
        text1 = self.extractor.extract_text_from_pdf_images(images1)
        text2 = self.extractor.extract_text_from_pdf_images(images2)
        
        # Analiza wizualna + hybrydowe porównanie
        results = []
        max_pages = max(len(images1), len(images2))
        
        # Stwórz folder na highlighted różnice
        os.makedirs("highlighted_diffs", exist_ok=True)
        
        for i in range(max_pages):
            page_num = i + 1
            
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
        """Hybrydowe porównanie pojedynczej strony"""
        
        # Analiza tekstowa (OCR)
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
        
        # Analiza wizualna (Computer Vision)
        visual_result = self.visual_comparator.compare_images(img1_path, img2_path)
        visual_similarity = visual_result['similarity']
        different_pixels = visual_result['different_pixels']
        total_pixels = visual_result['total_pixels']
        has_visual_differences = different_pixels > 0
        
        # Stwórz highlighted diff
        highlighted_path = f"highlighted_diffs/page_{page_num}_diff.png"
        self.visual_comparator.create_highlighted_diff(img1_path, img2_path, highlighted_path)
        
        # Kombinacja wyników (60% vision, 40% OCR)
        overall_similarity = (visual_similarity * 0.6) + (text_similarity * 0.4)
        
        return HybridComparisonResult(
            page_number=page_num,
            text_differences=text_differences,
            text_similarity_score=text_similarity,
            has_text_differences=has_text_differences,
            visual_similarity_score=visual_similarity,
            different_pixels=different_pixels,
            total_pixels=total_pixels,
            has_visual_differences=has_visual_differences,
            overall_similarity=overall_similarity,
            highlighted_diff_path=highlighted_path
        )

# ===== STREAMLIT APP =====

# Tytuł aplikacji
st.title("🔍 Hybrydowy System Porównywania PDF")
st.markdown("**Profesjonalne wykrywanie różnic w dokumentach graficznych**")
st.markdown("*Technologia: Computer Vision + OCR*")

# Sidebar z informacjami
st.sidebar.header("ℹ️ O systemie")
st.sidebar.markdown("""
**Hybrydowa technologia:**
- 🎯 60% Computer Vision
- 📝 40% OCR (rozpoznawanie tekstu)

**Wykrywa:**
- ✅ Zmiany tekstu
- ✅ Przesunięcia elementów
- ✅ Zmiany kolorów
- ✅ Dodane/usunięte grafiki
- ✅ Różnice w fontach

**Wyniki:**
- 📄 Szczegółowy raport tekstowy
- 🖼️ Obrazy z podświetlonymi różnicami
- 📊 Metryki podobieństwa
""")

# Główna aplikacja
def main():
    st.header("📤 Wgraj pliki PDF do porównania")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Pierwszy PDF")
        pdf1 = st.file_uploader("Wybierz pierwszy plik PDF", type="pdf", key="pdf1")
        
    with col2:
        st.subheader("📄 Drugi PDF")
        pdf2 = st.file_uploader("Wybierz drugi plik PDF", type="pdf", key="pdf2")
    
    if pdf1 and pdf2:
        st.success("✅ Pliki wgrane pomyślnie!")
        
        # Przycisk analizy
        if st.button("🚀 Rozpocznij analizę", type="primary"):
            analyze_pdfs(pdf1.read(), pdf2.read())

def analyze_pdfs(pdf1_bytes, pdf2_bytes):
    """Główna funkcja analizy"""
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Inicjalizacja
        status_text.text("🔧 Inicjalizacja systemu...")
        progress_bar.progress(10)
        
        comparator = HybridComparator()
        
        # Analiza
        status_text.text("🔍 Analiza hybrydowa w toku...")
        progress_bar.progress(30)
        
        results = comparator.compare_pdfs_hybrid(pdf1_bytes, pdf2_bytes)
        
        progress_bar.progress(100)
        status_text.text("✅ Analiza zakończona!")
        
        # Wyświetl wyniki
        if results:
            display_results(results)
        else:
            st.error("❌ Nie udało się przeanalizować PDF-ów")
        
    except Exception as e:
        st.error(f"❌ Błąd podczas analizy: {e}")

def display_results(results):
    """Wyświetla wyniki analizy"""
    
    st.header("📊 Wyniki analizy")
    
    # Podsumowanie
    pages_with_differences = sum(1 for r in results if r.overall_similarity < 1.0)
    avg_similarity = sum(r.overall_similarity for r in results) / len(results)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Stron", len(results))
    with col2:
        st.metric("⚠️ Z różnicami", pages_with_differences)
    with col3:
        st.metric("🎯 Podobieństwo", f"{avg_similarity:.1%}")
    with col4:
        critical = sum(1 for r in results if r.overall_similarity < 0.5)
        st.metric("🔴 Krytyczne", critical)
    
    # Szczegóły stron
    st.subheader("📋 Szczegóły stron")
    
    for result in results:
        with st.expander(f"📄 Strona {result.page_number} - Podobieństwo: {result.overall_similarity:.1%}"):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Metryki:**")
                st.write(f"👁️ Wizualne: {result.visual_similarity_score:.1%}")
                st.write(f"📝 Tekstowe: {result.text_similarity_score:.1%}")
                st.write(f"🎯 Ogólne: {result.overall_similarity:.1%}")
                
                # Klasyfikacja
                if result.overall_similarity < 0.5:
                    st.error("🔴 Różnice krytyczne")
                elif result.overall_similarity < 0.9:
                    st.warning("🟡 Różnice średnie")
                elif result.overall_similarity < 1.0:
                    st.info("🟢 Różnice drobne")
                else:
                    st.success("✅ Identyczne")
            
            with col2:
                # Pokaż highlighted obraz jeśli istnieje
                if os.path.exists(result.highlighted_diff_path):
                    st.write("**Różnice wizualne:**")
                    image = Image.open(result.highlighted_diff_path)
                    st.image(image, caption="Czerwone = różnice", use_column_width=True)

if __name__ == "__main__":
    main()