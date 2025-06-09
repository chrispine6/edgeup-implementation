import os
import base64
import requests
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def extract_text_from_image(image_source):
    try:
        if os.path.exists(image_source):
            base64_image = encode_image(image_source)
            image_url = f"data:image/jpeg;base64,{base64_image}"
        else:
            image_url = image_source
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "extract all text from this image. preserve formatting and structure. return only the extracted text."
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
        return extracted_text if extracted_text else "no text found in image"
    except Exception as e:
        return f"error: {str(e)}"

if __name__ == "__main__":
    image_path = ""
    if image_path and os.path.exists(image_path):
        result = extract_text_from_image(image_path)
        print("extracted text:")
        print(result)
    else:
        print("please provide a valid image path to test the ocr functionality.")
