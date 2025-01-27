
import fitz  # PyMuPDF
import os
import json
import pandas as pd
import logging
import uuid
from typing import List, Optional, Dict, Tuple
import datetime


# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def generate_unique_id(prefix: str) -> str:
    """
    Generate a unique identifier with a specified prefix.

    Parameters:
    - prefix (str): The prefix to use for the ID.

    Returns:
    - str: A unique identifier string with the given prefix.
    """
    return f"{prefix}_{uuid.uuid4().hex}"



def save_json(file_path: str, data: dict):
    """
    Save data to a JSON file.

    Parameters:
    - file_path (str): The path to the file where data should be saved.
    - data (dict): The data to save.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    logging.info(f"Data saved successfully to '{file_path}'.")



def extract_text_from_pdf(input_path: str) -> Optional[List[str]]:
    """
    Extract text from each page of a PDF using PyMuPDF.

    Parameters:
    - input_path (str): Path to the input PDF file.

    Returns:
    - Optional[List[str]]: List containing text of each page or None if an error occurs.
    """
    try:
        logging.info(f"Opening PDF: '{input_path}'")
        doc = fitz.open(input_path)
        text_pages = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            text_pages.append(text)
            logging.debug(f"Extracted text from page {page_num + 1}")
        return text_pages
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None



def parse_pdf_to_json(
    input_path: str,
    output_dir: str = "output",
    overwrite: bool = False
) -> Optional[str]:
    """
    Parses a PDF file and extracts all text into a JSON file.

    Parameters:
    - input_path (str): Path to the input PDF file.
    - output_dir (str): Directory where the output JSON will be saved.
    - overwrite (bool): If set to True, overwrites existing output files.

    Returns:
    - Optional[str]: Path to the generated JSON file or None if an error occurs.
    """
    # Validate input file path
    if not os.path.isfile(input_path):
        logging.error(f"Input file '{input_path}' does not exist.")
        return None

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    base_filename = os.path.splitext(os.path.basename(input_path))[0]
    output_json_file = os.path.join(output_dir, f"parsed_{base_filename}.json")

    # Skip if output file already exists and overwrite is False
    if not overwrite and os.path.exists(output_json_file):
        logging.warning(f"Output file '{output_json_file}' already exists. Use overwrite=True to process again.")
        return output_json_file

    # Extract text from PDF
    text_pages = extract_text_from_pdf(input_path)
    if text_pages is None:
        logging.error("Failed to extract text from the PDF document.")
        return None

    # Prepare the JSON structure
    pdf_json = {
        'filename': base_filename.strip(),
        'pages': []
    }

    for idx, page_text in enumerate(text_pages):
        page_dict = {
            'page_number': idx + 1,
            'content': page_text.strip()
        }
        pdf_json['pages'].append(page_dict)
        logging.debug(f"Added text for page {idx + 1} to JSON structure.")

    # Save the output JSON file
    save_json(output_json_file, pdf_json)

    logging.info(f"PDF parsing completed successfully and saved to '{output_json_file}'.")
    return output_json_file





def get_todays_date() -> str:
    """Return today's date in YYYY-MM-DD format."""
    return datetime.datetime.today().strftime('%Y-%m-%d')


if __name__ == "__main__":
    os.listdir("../papers2")
    # Get today's date
    todays_date = get_todays_date()
    pdfs = [
        f"../papers2/{todays_date}/{file}" 
        for file in os.listdir(f"../papers2/{todays_date}") 
        if file.endswith(".pdf")
    ]
    print(pdfs)


    for pdf in pdfs:
        output_json_path = parse_pdf_to_json(pdf, overwrite=True)
        if output_json_path:
            logging.info(f"Extracted text saved to: {output_json_path}")
        else:
            logging.error("Failed to extract text from the PDF.")





