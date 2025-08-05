from hybrid_comparator import HybridComparator, HybridComparisonResult
from datetime import datetime
from typing import List
import os

class HybridReportGenerator:
    def __init__(self):
        self.comparator = HybridComparator()
    
    def generate_hybrid_report(self, pdf1_path: str, pdf2_path: str, output_file: str = None):
        """
        Generuje kompletny hybrydowy raport (OCR + Vision)
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"hybrid_report_{timestamp}.txt"
        
        # Wykonaj hybrydowe porównanie
        results = self.comparator.compare_pdfs_hybrid(pdf1_path, pdf2_path)
        
        # Generuj raport
        report_content = self._create_hybrid_report(pdf1_path, pdf2_path, results)
        
        # Zapisz do pliku
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 Hybrydowy raport zapisany: {output_file}")
        return output_file, results
    
    def _create_hybrid_report(self, pdf1_path: str, pdf2_path: str, results: List[HybridComparisonResult]) -> str:
        """
        Tworzy kompletny hybrydowy raport
        """
        report = []
        
        # Nagłówek raportu
        report.append("=" * 80)
        report.append("HYBRYDOWY RAPORT PORÓWNANIA PDF (OCR + COMPUTER VISION)")
        report.append("=" * 80)
        report.append(f"Data analizy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"PDF 1: {pdf1_path}")
        report.append(f"PDF 2: {pdf2_path}")
        report.append(f"Metoda: Hybrydowa (60% Computer Vision + 40% OCR)")
        report.append("")
        
        # Podsumowanie wykonawcze
        pages_with_differences = sum(1 for r in results if r.overall_similarity < 1.0)
        avg_overall = sum(r.overall_similarity for r in results) / len(results) if results else 0
        avg_visual = sum(r.visual_similarity_score for r in results) / len(results) if results else 0
        avg_text = sum(r.text_similarity_score for r in results) / len(results) if results else 0
        
        report.append("PODSUMOWANIE WYKONAWCZE")
        report.append("-" * 40)
        report.append(f"Łączna liczba stron: {len(results)}")
        report.append(f"Strony z różnicami: {pages_with_differences}")
        report.append(f"Strony identyczne: {len(results) - pages_with_differences}")
        report.append(f"Średnie podobieństwo OGÓLNE: {avg_overall:.2%}")
        report.append(f"Średnie podobieństwo WIZUALNE: {avg_visual:.2%}")
        report.append(f"Średnie podobieństwo TEKSTOWE: {avg_text:.2%}")
        report.append("")
        
        # Klasyfikacja różnic
        critical_pages = [r for r in results if r.overall_similarity < 0.5]
        moderate_pages = [r for r in results if 0.5 <= r.overall_similarity < 0.9]
        minor_pages = [r for r in results if 0.9 <= r.overall_similarity < 1.0]
        
        report.append("KLASYFIKACJA RÓŻNIC (na podstawie analizy hybrydowej)")
        report.append("-" * 50)
        report.append(f"🔴 Różnice krytyczne (< 50%): {len(critical_pages)} stron")
        report.append(f"🟡 Różnice średnie (50-90%): {len(moderate_pages)} stron")
        report.append(f"🟢 Różnice drobne (90-99%): {len(minor_pages)} stron")
        report.append("")
        
        # Szczegółowa analiza strona po stronie
        report.append("SZCZEGÓŁOWA ANALIZA HYBRYDOWA STRONA PO STRONIE")
        report.append("=" * 60)
        
        for result in results:
            report.append(f"\nSTRONA {result.page_number}")
            report.append("-" * 30)
            
            # Wyniki hybrydowe
            report.append(f"🎯 PODOBIEŃSTWO OGÓLNE: {result.overall_similarity:.2%}")
            report.append(f"   👁️ Analiza wizualna (CV): {result.visual_similarity_score:.2%}")
            report.append(f"   📝 Analiza tekstowa (OCR): {result.text_similarity_score:.2%}")
            
            # Klasyfikacja
            if result.overall_similarity < 0.5:
                severity = "🔴 KRYTYCZNA"
            elif result.overall_similarity < 0.9:
                severity = "🟡 ŚREDNIA"
            elif result.overall_similarity < 1.0:
                severity = "🟢 DROBNA"
            else:
                severity = "✅ IDENTYCZNA"
            
            report.append(f"⚠️ Klasyfikacja: {severity}")
            
            # Szczegóły wizualne
            report.append(f"\n📊 ANALIZA WIZUALNA:")
            report.append(f"   Różne piksele: {result.different_pixels:,}")
            report.append(f"   Całkowite piksele: {result.total_pixels:,}")
            report.append(f"   Procent różnic: {(result.different_pixels/result.total_pixels)*100:.2f}%")
            report.append(f"   Highlighted diff: {result.highlighted_diff_path}")
            
            # Szczegóły tekstowe
            if result.has_text_differences:
                report.append(f"\n📝 ANALIZA TEKSTOWA:")
                report.append(f"   Liczba linii z różnicami: {len(result.text_differences)}")
                
                # Pokaż różnice tekstowe
                for diff in result.text_differences:
                    if diff.startswith('---') or diff.startswith('+++'):
                        continue
                    elif diff.startswith('-'):
                        report.append(f"   USUNIĘTO: {diff[1:].strip()}")
                    elif diff.startswith('+'):
                        report.append(f"   DODANO:   {diff[1:].strip()}")
            else:
                report.append(f"\n📝 ANALIZA TEKSTOWA: Brak różnic tekstowych")
            
            report.append("")
        
        # Rekomendacje
        report.append("REKOMENDACJE")
        report.append("-" * 20)
        if pages_with_differences == 0:
            report.append("✅ Dokumenty są identyczne - brak działań wymaganych.")
        else:
            report.append(f"⚠️ Wykryto różnice na {pages_with_differences} stronach:")
            if critical_pages:
                report.append(f"  🔴 Priorytet KRYTYCZNY: Strony {[p.page_number for p in critical_pages]}")
            if moderate_pages:
                report.append(f"  🟡 Priorytet ŚREDNI: Strony {[p.page_number for p in moderate_pages]}")
            if minor_pages:
                report.append(f"  🟢 Priorytet NISKI: Strony {[p.page_number for p in minor_pages]}")
            
            report.append(f"\n📸 WIZUALIZACJE:")
            report.append(f"  Sprawdź folder 'highlighted_diffs/' - zawiera obrazy z podświetlonymi różnicami")
            report.append(f"  Czerwone obszary = wykryte różnice")
        
        report.append("")
        report.append("=" * 80)
        report.append("KONIEC HYBRYDOWEGO RAPORTU")
        report.append("=" * 80)
        
        return "\n".join(report)

# Test generatora
if __name__ == "__main__":
    generator = HybridReportGenerator()
    print("Hybrid Report Generator gotowy!")