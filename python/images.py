import os
import base64
import requests
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Set OpenAI API key from environment
openai.api_key = os.getenv('OPENAI_API_KEY')

def encode_image(image_path):
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Base64 encoded image string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# API request to OpenAI 
def extract_text_from_image(image_source):
    """
    Extract text from an image using OpenAI's vision model.
    
    Args:
        image_source: Either a file path or base64 encoded image string
        
    Returns:
        str: Extracted text from the image
    """
    try:
        # Check if image_source is a file path or base64 string
        if os.path.exists(image_source):
            # It's a file path, encode it
            base64_image = encode_image(image_source)
            image_url = f"data:image/jpeg;base64,{base64_image}"
        else:
            # Assume it's already a URL or base64 string
            image_url = image_source
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Extract all text from this image. Preserve formatting and structure. Return only the extracted text."
                        },
                        {
                            "type": "image_url", 
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        extracted_text = response.choices[0].message.content
        return extracted_text if extracted_text else "No text found in image"
        
    except Exception as e:
        return f"Error: {str(e)}"

# Example usage (commented out to prevent automatic execution)
if __name__ == "__main__":
    # Example usage - replace with your image path
    image_path = ""  # Add your image path here
    
    if image_path and os.path.exists(image_path):
        result = extract_text_from_image(image_path)
        print("Extracted text:")
        print(result)
    else:
        print("Please provide a valid image path to test the OCR functionality.")
