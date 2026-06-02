import os
from pypdf import PdfReader

# =========================
# ABSOLUTE BASE DIRECTORY
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PDF_FOLDER = os.path.join(BASE_DIR, "pdfs")
TEXT_FOLDER = os.path.join(BASE_DIR, "extracted_text")

# =========================
# CREATE OUTPUT FOLDER
# =========================

os.makedirs(TEXT_FOLDER, exist_ok=True)

# =========================
# FIND PDF FILES
# =========================

pdf_files = [
    file for file in os.listdir(PDF_FOLDER)
    if file.lower().endswith(".pdf")
]

print("\n====================")
print("PDF FILES FOUND")
print("====================")
print(len(pdf_files))

# =========================
# EXTRACT TEXT
# =========================

processed = 0
skipped = 0
failed = 0

for pdf_name in pdf_files:

    try:

        pdf_path = os.path.join(PDF_FOLDER, pdf_name)

        output_name = os.path.splitext(pdf_name)[0] + ".txt"

        output_path = os.path.join(TEXT_FOLDER, output_name)

        # =========================
        # SKIP EXISTING TEXT
        # =========================

        if os.path.exists(output_path):

            print(f"SKIPPING TEXT: {output_name}")
            skipped += 1
            continue

        print("\nPROCESSING:")
        print(pdf_name)

        reader = PdfReader(pdf_path)

        full_text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                full_text += page_text + "\n"

        with open(output_path, "w", encoding="utf-8") as text_file:

            text_file.write(full_text)

        print("SAVED:")
        print(output_path)

        processed += 1

    except Exception as e:

        print("\nFAILED:")
        print(pdf_name)
        print(e)

        failed += 1

# =========================
# DONE
# =========================

print("\n====================")
print("PDF TEXT EXTRACTION COMPLETE")
print("====================")
print(f"Processed: {processed}")
print(f"Skipped: {skipped}")
print(f"Failed: {failed}")