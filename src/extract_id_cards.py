#!/usr/bin/env python3
"""
ID Card Extractor
Extracts front and back images from Chinese ID card PDFs in two formats:
- Format 1: 2-page PDF (page 1 = front, page 2 = back)
- Format 2: 1-page PDF (both sides on same page)
"""

import os
import sys
from pathlib import Path
import logging
from datetime import datetime

try:
    import fitz  # PyMuPDF
    from PIL import Image
    import pytesseract
except ImportError as e:
    print("Installing required packages...")
    print("Using proxy: socks5://127.0.0.1:10808")
    
    # Set proxy environment variables for pip
    proxy_url = "socks5://127.0.0.1:10808"
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
    os.environ['http_proxy'] = proxy_url
    os.environ['https_proxy'] = proxy_url
    
    # First, install PySocks for SOCKS5 proxy support
    print("\nStep 1: Installing PySocks for SOCKS5 proxy support...")
    pysocks_cmd = f'pip install --proxy={proxy_url} PySocks'
    print(f"Running: {pysocks_cmd}")
    os.system(pysocks_cmd)
    
    # Check if wrong 'fitz' package is installed and remove it
    print("\nStep 2: Checking for conflicting packages...")
    if "No module named 'frontend'" in str(e):
        print("Detected wrong 'fitz' package. Uninstalling...")
        os.system('pip uninstall -y fitz')
    
    # Install required packages with proxy
    print("\nStep 3: Installing PyMuPDF, Pillow, and pytesseract...")
    install_cmd = f'pip install --proxy={proxy_url} PyMuPDF Pillow pytesseract'
    print(f"Running: {install_cmd}")
    result = os.system(install_cmd)
    
    if result != 0:
        print("\nWarning: Package installation failed. Please install manually:")
        print("  1. pip install PySocks")
        print("  2. pip uninstall -y fitz")
        print("  3. pip install --proxy=socks5://127.0.0.1:10808 PyMuPDF Pillow pytesseract")
    
    # Note for Windows Tesseract installation
    print("\nNote: For OCR functionality, please install Tesseract OCR manually on Windows:")
    print("  1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("  2. Install and add to PATH, or set pytesseract.pytesseract.tesseract_cmd")
    print("  3. Install Chinese language data during installation\n")
    
    print("Please restart the script after installation completes.\n")
    sys.exit(1)

# Get project root directory (parent of src directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Setup logging in .archive/logs directory
log_dir = PROJECT_ROOT / ".archive" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "id_extraction.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def detect_card_side(page):
    """
    Detect if a page is the front or back of an ID card.
    Front side indicators: photo, name (姓名), ID number (公民身份号码), birth date (出生)
    Back side indicators: issuing authority (签发机关), validity period (有效期限)
    Returns: 'front', 'back', or 'unknown'
    """
    try:
        # First try to get text directly
        text = page.get_text()
        
        # If very little text found, it's likely a scanned image - try OCR
        if len(text.strip()) < 20:
            try:
                import pytesseract
                from PIL import Image
                import io
                
                # Convert page to image and run OCR
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution for OCR
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Run OCR with Chinese language support
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                logger.debug(f"Used OCR, extracted text length: {len(text)}")
            except ImportError:
                logger.debug("Tesseract not available, using text extraction only")
            except Exception as ocr_error:
                logger.debug(f"OCR failed: {str(ocr_error)}")
        
        # Count indicators for each side
        front_indicators = 0
        back_indicators = 0
        
        # Front side indicators
        front_keywords = ['姓名', '性别', '民族', '出生', '住址', '公民身份号码', '身份证']
        for keyword in front_keywords:
            if keyword in text:
                front_indicators += 1
        
        # Back side indicators  
        back_keywords = ['签发机关', '有效期限', '发证机关', '签发', '有效']
        for keyword in back_keywords:
            if keyword in text:
                back_indicators += 1
        
        # Special check: if it has validity dates pattern (YYYY.MM.DD-YYYY.MM.DD)
        import re
        if re.search(r'\d{4}[.\s年]+\d{1,2}[.\s月]+\d{1,2}[-日\s]+\d{4}[.\s年]+\d{1,2}[.\s月]+\d{1,2}', text):
            back_indicators += 2
        
        logger.debug(f"Front indicators: {front_indicators}, Back indicators: {back_indicators}")
        
        # Determine side based on indicators
        if front_indicators > back_indicators:
            return 'front'
        elif back_indicators > front_indicators:
            return 'back'
        else:
            return 'unknown'
            
    except Exception as e:
        logger.error(f"Error detecting card side: {str(e)}")
        return 'unknown'


def detect_pdf_format(pdf_path):
    """
    Detect which format the PDF is in.
    Returns: 'format1' (2 pages), 'format2' (1 page), or None if invalid
    """
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        
        if page_count == 2:
            return 'format1'
        elif page_count == 1:
            return 'format2'
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error detecting format for {pdf_path}: {str(e)}")
        return None


def extract_format1(pdf_path, output_dir, base_name):
    """
    Extract from Format 1: 2-page PDF
    Automatically detects which page is front or back
    """
    try:
        doc = fitz.open(pdf_path)
        
        # Detect which page is which
        page1_side = detect_card_side(doc[0])
        page2_side = detect_card_side(doc[1])
        
        logger.info(f"Page 1 detected as: {page1_side}")
        logger.info(f"Page 2 detected as: {page2_side}")
        
        # Create mapping of page index to side
        page_mapping = {}
        
        if page1_side == 'front':
            page_mapping['front'] = 0
            page_mapping['back'] = 1
        elif page1_side == 'back':
            page_mapping['front'] = 1
            page_mapping['back'] = 0
        elif page2_side == 'front':
            page_mapping['front'] = 1
            page_mapping['back'] = 0
        elif page2_side == 'back':
            page_mapping['front'] = 0
            page_mapping['back'] = 1
        else:
            # If we can't detect, default to page 1 = front, page 2 = back
            logger.warning("Could not definitively detect card sides, using default order (page 1=front, page 2=back)")
            page_mapping['front'] = 0
            page_mapping['back'] = 1
        
        # Extract front
        page = doc[page_mapping['front']]
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
        front_path = output_dir / f"{base_name}_front.png"
        pix.save(str(front_path))
        logger.info(f"Saved front (from page {page_mapping['front'] + 1}): {front_path}")
        
        # Extract back
        page = doc[page_mapping['back']]
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
        back_path = output_dir / f"{base_name}_back.png"
        pix.save(str(back_path))
        logger.info(f"Saved back (from page {page_mapping['back'] + 1}): {back_path}")
        
        doc.close()
        return True
        
    except Exception as e:
        logger.error(f"Error extracting Format 1 from {pdf_path}: {str(e)}")
        return False


def extract_format2(pdf_path, output_dir, base_name):
    """
    Extract from Format 2: 1-page PDF with both sides
    Automatically detects which half is front or back
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        # Get full page as image
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        width, height = img.size
        mid_height = height // 2
        
        # Try to detect which half is which by analyzing text in each half
        # Create temporary sub-pages for analysis
        rect_top = fitz.Rect(0, 0, page.rect.width, page.rect.height / 2)
        rect_bottom = fitz.Rect(0, page.rect.height / 2, page.rect.width, page.rect.height)
        
        text_top = page.get_text(clip=rect_top)
        text_bottom = page.get_text(clip=rect_bottom)
        
        # If very little text, try OCR on image crops
        if len(text_top.strip()) < 20 or len(text_bottom.strip()) < 20:
            try:
                import pytesseract
                
                # OCR top half
                top_img = img.crop((0, 0, width, mid_height))
                text_top = pytesseract.image_to_string(top_img, lang='chi_sim+eng')
                
                # OCR bottom half
                bottom_img = img.crop((0, mid_height, width, height))
                text_bottom = pytesseract.image_to_string(bottom_img, lang='chi_sim+eng')
                
                logger.debug("Used OCR for Format 2 detection")
            except Exception as ocr_error:
                logger.debug(f"OCR not available for Format 2: {str(ocr_error)}")
        
        # Analyze each half
        top_indicators = 0
        bottom_indicators = 0
        
        # Check for front indicators
        front_keywords = ['姓名', '性别', '民族', '出生', '住址', '公民身份号码']
        for keyword in front_keywords:
            if keyword in text_top:
                top_indicators += 1
            if keyword in text_bottom:
                bottom_indicators += 1
        
        # Check for back indicators (these reduce the score)
        back_keywords = ['签发机关', '有效期限', '发证机关', '签发', '有效']
        for keyword in back_keywords:
            if keyword in text_top:
                top_indicators -= 1
            if keyword in text_bottom:
                bottom_indicators -= 1
        
        # Check for validity date pattern
        import re
        if re.search(r'\d{4}[.\s年]+\d{1,2}[.\s月]+\d{1,2}[-日\s]+\d{4}[.\s年]+\d{1,2}[.\s月]+\d{1,2}', text_top):
            top_indicators -= 2
        if re.search(r'\d{4}[.\s年]+\d{1,2}[.\s月]+\d{1,2}[-日\s]+\d{4}[.\s年]+\d{1,2}[.\s月]+\d{1,2}', text_bottom):
            bottom_indicators -= 2
        
        logger.info(f"Top half score: {top_indicators}, Bottom half score: {bottom_indicators}")
        
        # Determine which half is front
        margin = int(height * 0.05)  # 5% margin
        
        if top_indicators > bottom_indicators:
            # Top is front, bottom is back
            logger.info("Detected: Top half = front, Bottom half = back")
            front_img = img.crop((0, 0, width, mid_height + margin))
            back_img = img.crop((0, mid_height - margin, width, height))
        else:
            # Bottom is front, top is back (or default if equal)
            if top_indicators == bottom_indicators:
                logger.warning("Could not definitively detect card sides, using default order (top=front, bottom=back)")
            else:
                logger.info("Detected: Bottom half = front, Top half = back")
            # For reverse order
            if bottom_indicators > top_indicators:
                front_img = img.crop((0, mid_height - margin, width, height))
                back_img = img.crop((0, 0, width, mid_height + margin))
            else:
                # Default: top = front
                front_img = img.crop((0, 0, width, mid_height + margin))
                back_img = img.crop((0, mid_height - margin, width, height))
        
        # Save images
        front_path = output_dir / f"{base_name}_front.png"
        front_img.save(str(front_path))
        logger.info(f"Saved front: {front_path}")
        
        back_path = output_dir / f"{base_name}_back.png"
        back_img.save(str(back_path))
        logger.info(f"Saved back: {back_path}")
        
        doc.close()
        return True
        
    except Exception as e:
        logger.error(f"Error extracting Format 2 from {pdf_path}: {str(e)}")
        return False


def process_pdf(pdf_path, output_dir):
    """
    Process a single PDF file
    """
    try:
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"File not found: {pdf_path}")
            return False
            
        if not pdf_path.suffix.lower() == '.pdf':
            logger.warning(f"Skipping non-PDF file: {pdf_path}")
            return False
        
        base_name = pdf_path.stem
        logger.info(f"Processing: {pdf_path.name}")
        
        # Detect format
        format_type = detect_pdf_format(pdf_path)
        
        if format_type is None:
            logger.error(f"UNSUPPORTED FORMAT: {pdf_path.name} - PDF must have exactly 1 or 2 pages")
            return False
        
        logger.info(f"Detected format: {format_type}")
        
        # Extract based on format
        if format_type == 'format1':
            success = extract_format1(pdf_path, output_dir, base_name)
        elif format_type == 'format2':
            success = extract_format2(pdf_path, output_dir, base_name)
        else:
            logger.error(f"Unknown format type: {format_type}")
            return False
        
        if success:
            logger.info(f"Successfully processed: {pdf_path.name}\n")
        else:
            logger.error(f"Failed to process: {pdf_path.name}\n")
            
        return success
        
    except Exception as e:
        logger.error(f"Unexpected error processing {pdf_path}: {str(e)}\n")
        return False


def process_directory(input_dir, output_dir):
    """
    Process all PDF files in a directory
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("="*60)
    logger.info(f"ID Card Extraction Started - {datetime.now()}")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("="*60 + "\n")
    
    # Get all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF file(s)\n")
    
    # Process each PDF
    success_count = 0
    error_count = 0
    
    for pdf_file in pdf_files:
        if process_pdf(pdf_file, output_dir):
            success_count += 1
        else:
            error_count += 1
    
    # Summary
    logger.info("="*60)
    logger.info("SUMMARY")
    logger.info(f"Total PDFs: {len(pdf_files)}")
    logger.info(f"Successfully processed: {success_count}")
    logger.info(f"Failed/Skipped: {error_count}")
    logger.info("="*60)
    
    if error_count > 0:
        logger.info(f"\nCheck log file for details: {log_file}")


if __name__ == "__main__":
    # Configuration - using project directory structure
    INPUT_DIR = PROJECT_ROOT / "inputs"
    OUTPUT_DIR = PROJECT_ROOT / "outputs"
    
    # Ensure directories exist
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run the extraction
    process_directory(INPUT_DIR, OUTPUT_DIR)