import os
import json
import datetime
import time
from openai import OpenAI
import base64
import tempfile
from PIL import Image
import io
import requests

def process_image_with_openai(api_key, base64_image, prompt, max_tokens=300, temperature=0.7):
    """
    Process an image using OpenAI's gpt-4o model
    
    Args:
        api_key (str): OpenAI API key
        base64_image (str): Base64-encoded image
        prompt (str): Prompt to send to the API
        max_tokens (int): Maximum tokens for the response
        temperature (float): Temperature parameter for the API
        
    Returns:
        str: The API response text
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Prepare the API request
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the multimodal model that supports image input
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        }
                    ],
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Extract and return the response content
        return response.choices[0].message.content
        
    except Exception as e:
        # Re-raise the exception with more context
        raise Exception(f"OpenAI API error: {str(e)}")

def edit_image_with_openai(api_key, image, prompt, size="1024x1024"):
    """
    Edit an image using OpenAI's gpt-image-1 model
    
    Args:
        api_key (str): OpenAI API key
        image (PIL.Image): The image to edit
        prompt (str): Instructions for how to edit the image
        size (str): Resolution of the output image. Options: "1024x1024" (default), "1792x1024", or "1024x1792"
        
    Returns:
        str: URL of the edited image
        
    Note:
        This function uses the gpt-image-1 model which can understand and
        transform images based on natural language prompts.
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Ensure image is in RGB mode
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Create a temporary file for the image with proper PNG extension
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_temp:
            # Save image as PNG
            image.save(img_temp, format="PNG")
            img_temp_path = img_temp.name
        
        # Make the API request to edit the image using gpt-image-1
        try:
            with open(img_temp_path, "rb") as img_file:
                # Following the exact format from the documentation
                response = client.images.edit(
                    model="gpt-image-1",
                    image=[img_file],  # Passed as a list as per the documentation
                    prompt=prompt,
                    size=size,  # Control output resolution
                    quality="high"  # Optional, but can be set to "high" for better quality
                )
            
            # Check for different response formats
            if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
                # If we have a base64 image, save it and return a local URL
                image_data = response.data[0].b64_json
                image_bytes = base64.b64decode(image_data)
                
                # Create a unique filename
                edited_image_path = os.path.join(tempfile.gettempdir(), f"edited_image_{int(time.time())}.png")
                
                # Save the image to a temporary file
                with open(edited_image_path, "wb") as f:
                    f.write(image_bytes)
                
                # Return the path to the saved image
                return edited_image_path
            
            # If URL is available in the response, return it
            elif hasattr(response.data[0], 'url') and response.data[0].url:
                return response.data[0].url
            
            # If neither is available, raise an error
            else:
                raise Exception("No image URL or data received in the response")
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(img_temp_path):
                    os.unlink(img_temp_path)
            except Exception as e:
                print(f"Warning: Failed to clean up temporary files: {e}")
        
    except Exception as e:
        # Re-raise the exception with more context
        raise Exception(f"OpenAI image edit error: {str(e)}")

def save_results_to_file(results, format_type="json"):
    """
    Save processing results to a file
    
    Args:
        results (list): List of result dictionaries
        format_type (str): 'json' or 'text'
        
    Returns:
        str: Path to the saved file
    """
    # Create a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Determine the desktop directory (or fallback to temp directory)
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(desktop_dir):
        desktop_dir = tempfile.gettempdir()
    
    if format_type == "json":
        # Save as JSON
        file_path = os.path.join(desktop_dir, f"image_analysis_{timestamp}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    else:
        # Save as plain text
        file_path = os.path.join(desktop_dir, f"image_analysis_{timestamp}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(f"Image: {result['image_path']}\n")
                f.write("-" * 50 + "\n")
                f.write(f"{result['response']}\n\n")
                f.write("=" * 70 + "\n\n")
    
    return file_path

def create_zip_of_edited_images(edited_images, original_images, image_paths):
    """
    Create a zip file containing all edited images
    
    Args:
        edited_images (dict): Dictionary of edited image paths or URLs
        original_images (list): List of original images
        image_paths (list): List of original image paths or names
        
    Returns:
        str: Path to the zip file, None if failed
    """
    try:
        import zipfile
        import tempfile
        import os
        from datetime import datetime
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a temporary directory for the images
        temp_dir = tempfile.mkdtemp()
        
        # Create a zip file
        zip_path = os.path.join(tempfile.gettempdir(), f"edited_images_{timestamp}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add each edited image to the zip file
            for img_index, img_data in edited_images.items():
                try:
                    # Get original image name
                    if img_index < len(image_paths):
                        orig_name = os.path.basename(image_paths[img_index])
                    else:
                        orig_name = f"image_{img_index+1}"
                    
                    # Create a filename for the edited image
                    edited_filename = f"edited_{orig_name}"
                    if not edited_filename.lower().endswith('.png'):
                        edited_filename += '.png'
                    
                    # Different handling based on if it's a URL or a file path
                    if isinstance(img_data, str):
                        if img_data.startswith(('http://', 'https://')):
                            # It's a URL, download the image
                            response = requests.get(img_data)
                            edited_image = Image.open(io.BytesIO(response.content))
                        else:
                            # It's a local file path
                            edited_image = Image.open(img_data)
                        
                        # Save the edited image to a temporary file
                        temp_file = os.path.join(temp_dir, edited_filename)
                        edited_image.save(temp_file, format="PNG")
                        
                        # Add the temporary file to the zip
                        zipf.write(temp_file, edited_filename)
                except Exception as e:
                    print(f"Error adding image {img_index} to zip: {e}")
                    continue
        
        return zip_path
    except Exception as e:
        print(f"Error creating zip file: {e}")
        return None
