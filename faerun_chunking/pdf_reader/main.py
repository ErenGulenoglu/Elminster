# Install: pip install pypdf
from pypdf import PdfReader

def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:  # sometimes extract_text() returns None
            # Clean up headers/footers if needed
            page_text = page_text.replace("\n", " ").strip()
            text += page_text + "\n\n"  # separate pages
        else:
            print(f"Warning: page {i+1} is empty or not readable.")
    return text

# Usage
def create_lore_txt(pdf_name:str):
    full_text = extract_pdf_text(f"./PDFs/{pdf_name}")
    print(full_text)
    print(f"Extracted {len(full_text.split())} words from PDF")
    with open(f"./Output/{pdf_name}.txt", 'w', encoding='utf-8') as f:
        f.write(full_text)

if __name__ == "__main__":
    create_lore_txt("The Making of a Mage.pdf")