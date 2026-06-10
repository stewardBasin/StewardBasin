import os
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PDF_FOLDER = os.path.join(BASE_DIR, "pdfs", "deq_uintah_2024_2026_real")
TEXT_FOLDER = os.path.join(BASE_DIR, "extracted_text", "deq_uintah_2024_2026")

os.makedirs(TEXT_FOLDER, exist_ok=True)

pdf_files = [file for file in os.listdir(PDF_FOLDER) if file.lower().endswith(".pdf")]

print(f"PDF files found: {len(pdf_files)}")

processed = 0
skipped = 0
failed = 0

for pdf_name in pdf_files:
    try:
        pdf_path = os.path.join(PDF_FOLDER, pdf_name)
        output_name = os.path.splitext(pdf_name)[0] + ".txt"
        output_path = os.path.join(TEXT_FOLDER, output_name)

        if os.path.exists(output_path):
            print(f"Skipping existing: {output_name}")
            skipped += 1
            continue

        print(f"Extracting: {pdf_name}")

        reader = PdfReader(pdf_path)
        full_text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

        with open(output_path, "w", encoding="utf-8") as text_file:
            text_file.write(full_text)

        processed += 1

    except Exception as e:
        print(f"FAILED: {pdf_name}")
        print(e)
        failed += 1

print("\nDone.")
print(f"Processed: {processed}")
print(f"Skipped: {skipped}")
print(f"Failed: {failed}")
print(f"Saved to: {TEXT_FOLDER}")
