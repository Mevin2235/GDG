import os
import fitz  # PyMuPDF
from PIL import Image
from google.cloud import vision
import io
import re

# Set your service account JSON key path
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:/Users/MEVIN/Downloads/effortless-edge-454405-k0-dbcbc18cd900.json"

# Initialize Vision client
client = vision.ImageAnnotatorClient()

def pdf_page_to_image(page, dpi=300):
    """Convert PDF page to PIL Image."""
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

def image_to_text_google_vision(pil_image):
    """Extract text from image using Google Vision."""
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    image = vision.Image(content=img_byte_arr)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        return texts[0].description
    else:
        return ""

def clean_and_structure_text(raw_text):
    """Clean OCR text and structure it into questions/answers."""
    # Remove unwanted symbols & extra spaces
    text = re.sub(r'[^\x00-\x7F]+', ' ', raw_text)  # Remove non-ASCII chars
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with single space
    text = text.strip()

    # Split into questions based on patterns (modify as needed)
    # Looks for "Q." or "Question" or "PART" to split
    split_pattern = re.compile(r'(Q\.|Question|UNIT TEST|PART-[A-Z])', re.IGNORECASE)

    # Find matches and rebuild the content
    parts = split_pattern.split(text)
    structured_output = ""
    
    # If it starts without a question label, the first item is garbage
    if parts[0].strip() == '':
        parts = parts[1:]

    # Recombine the prefix with the content
    for i in range(0, len(parts), 2):
        label = parts[i].strip()
        content = parts[i+1].strip() if i+1 < len(parts) else ""
        structured_output += f"\n\n=== {label} ===\n{content}\n"

    return structured_output

def process_pdf_with_structured_output(pdf_path, output_text_file=None):
    """Process PDF, extract text and structure it."""
    doc = fitz.open(pdf_path)
    all_text = ""

    print(f"Total pages found: {len(doc)}\n")

    for page_num in range(len(doc)):
        print(f"\nProcessing page {page_num + 1}...")

        # Convert to image
        page = doc.load_page(page_num)
        pil_img = pdf_page_to_image(page)

        # Extract raw OCR text
        raw_text = image_to_text_google_vision(pil_img)

        print(f"\n=== Raw OCR Output for Page {page_num + 1} ===\n")
        print(raw_text)

        # Clean and structure the text
        structured_text = clean_and_structure_text(raw_text)

        print(f"\n=== Structured Output for Page {page_num + 1} ===\n")
        print(structured_text)

        # Append
        all_text += f"\nPage {page_num + 1}:\n{structured_text}\n"

    # Save to file
    if output_text_file:
        with open(output_text_file, "w", encoding="utf-8") as f:
            f.write(all_text)
        print(f"\n✅ Structured text saved to: {output_text_file}")

    return all_text

# Example usage
if __name__ == "__main__":
    pdf_file_path = r"C:/Users/MEVIN/Downloads/ans.pdf"
    output_file = "structured_extracted_text.txt"

    if os.path.exists(pdf_file_path):
        process_pdf_with_structured_output(pdf_file_path, output_text_file=output_file)
    else:
        print("❌ PDF file not found. Check the path.")
