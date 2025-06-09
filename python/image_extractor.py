import os
import base64
import logging
from PIL import Image
import openai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_API_KEY')

def encode_image(image_path):
    # encode an image file to base64 string
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encode image {image_path}: {str(e)}")
        raise

def validate_image(image_path):
    # validate that the file is a supported image format
    try:
        with Image.open(image_path) as img:
            supported_formats = ['JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'WEBP']
            return img.format in supported_formats
    except Exception as e:
        logger.warning(f"Image validation failed for {image_path}: {str(e)}")
        return False

def extract_text_from_image(image_path):
    # extract text from an image using openai's vision model
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    if not validate_image(image_path):
        raise ValueError(f"Unsupported image format: {image_path}")
    
    try:
        logger.info(f"Processing image: {image_path}")
        base64_image = encode_image(image_path)
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Extract all text from this image. Preserve the formatting and structure as much as possible. If there are tables, maintain the tabular structure. If there are multiple columns, indicate the column breaks clearly. Return only the extracted text without any additional commentary."
                        },
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )
        extracted_text = response.choices[0].message.content
        if not extracted_text or extracted_text.strip() == "":
            logger.warning(f"No text extracted from image: {image_path}")
            return "No text found in image"
        logger.info(f"Successfully extracted text from {image_path}")
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from image {image_path}: {str(e)}")
        raise Exception(f"OCR processing failed: {str(e)}")

def extract_text_from_images(image_paths):
    # extract text from multiple images
    results = []
    for i, image_path in enumerate(image_paths):
        try:
            logger.info(f"Processing image {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")
            text = extract_text_from_image(image_path)
            results.append(text)
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {str(e)}")
            results.append(f"Error processing image: {str(e)}")
    return results

def extract_text_from_image_as_pages(image_path):
    # extract text from an image and return as a single-page list for compatibility with pdf processing
    text = extract_text_from_image(image_path)
    return [text]
