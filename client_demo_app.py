import os
# Konfiguracja dla Streamlit Cloud
if not os.path.exists('/usr/bin/tesseract'):
    # Lokalna ścieżka
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'



import streamlit as st
from hybrid_report_generator import HybridReportGenerator
import os
from PIL import Image
import zipfile
import io

# Konfiguracja strony
st.set_page_config(
    page_title="PDF Comparison System - Demo",
    page_icon="📄",
    layout="wide"
)

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
        # Zapisz pliki tymczasowo
        with open("temp_pdf1.pdf", "wb") as f:
            f.write(pdf1.read())
        with open("temp_pdf2.pdf", "wb") as f:
            f.write(pdf2.read())
        
        st.success("✅ Pliki wgrane pomyślnie!")
        
        # Przycisk analizy
        if st.button("🚀 Rozpocznij analizę", type="primary"):
            analyze_pdfs()

def analyze_pdfs():
    """Główna funkcja analizy"""
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Inicjalizacja
        status_text.text("🔧 Inicjalizacja systemu...")
        progress_bar.progress(10)
        
        generator = HybridReportGenerator()
        
        # Analiza
        status_text.text("🔍 Analiza hybrydowa w toku...")
        progress_bar.progress(30)
        
        report_file, results = generator.generate_hybrid_report("temp_pdf1.pdf", "temp_pdf2.pdf")
        
        progress_bar.progress(100)
        status_text.text("✅ Analiza zakończona!")
        
        # Wyświetl wyniki
        display_results(report_file, results)
        
    except Exception as e:
        st.error(f"❌ Błąd podczas analizy: {e}")

def display_results(report_file, results):
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
    
    # Download raportu
    st.subheader("📥 Pobierz wyniki")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Raport tekstowy
        if os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            st.download_button(
                label="📄 Pobierz raport tekstowy",
                data=report_content,
                file_name=report_file,
                mime="text/plain"
            )
    
    with col2:
        # Zip z obrazami
        if os.path.exists("highlighted_diffs"):
            zip_buffer = create_images_zip()
            st.download_button(
                label="🖼️ Pobierz obrazy (ZIP)",
                data=zip_buffer,
                file_name="highlighted_differences.zip",
                mime="application/zip"
            )

def create_images_zip():
    """Tworzy ZIP z highlighted obrazami"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename in os.listdir("highlighted_diffs"):
            if filename.endswith('.png'):
                zip_file.write(
                    os.path.join("highlighted_diffs", filename),
                    filename
                )
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

if __name__ == "__main__":
    main()