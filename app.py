import streamlit as st

# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="OpenAI Image Editor",
    page_icon="🖼️",
    layout="wide"
)

import os
import base64
from PIL import Image
import io
import json
import requests
from utils import process_image_with_openai, save_results_to_file, edit_image_with_openai, create_zip_of_edited_images
import time
import hmac
import logging
from datetime import datetime
# Temporarily disabled rate limiter for deployment
# from streamlit_limiter import limiter

# Configure logging
log_dir = 'logs'
try:
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')
    
    # Create a file handler that writes to the log file
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Get the root logger and add the file handler
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler())
    
    # Test the logger
    logger.info("Application started - Logger initialized successfully")
    
except Exception as e:
    print(f"Error setting up logging: {str(e)}")
    raise

def log_activity(action: str, success: bool, **kwargs):
    """Helper function to log activities"""
    try:
        # Try to get HTTP headers if available
        headers = st.experimental_get_http_headers()
        ip = headers.get('X-Forwarded-For', 'unknown')
        user_agent = headers.get('User-Agent', 'unknown')
    except:
        # Fallback if headers are not available
        ip = 'not_available'
        user_agent = 'not_available'
    
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'success': success,
        'ip': ip,
        'user_agent': user_agent,
        **kwargs
    }
    logger.info(f"{action} - Success: {success} - IP: {ip}")
    return log_data

def check_password():
    """Returns `True` if the user had the correct password."""
    
    # Initialize session state if not exists
    if 'password_correct' not in st.session_state:
        st.session_state['password_correct'] = False
        st.session_state['login_attempts'] = 0
        st.session_state['last_attempt_time'] = 0
    
    # Check rate limiting
    current_time = time.time()
    if st.session_state.get('login_attempts', 0) >= 5:  # Max 5 attempts
        if current_time - st.session_state['last_attempt_time'] < 300:  # 5 minute cooldown
            wait_time = int(300 - (current_time - st.session_state['last_attempt_time']))
            st.error(f"Too many failed attempts. Please try again in {wait_time} seconds.")
            return False
        else:
            # Reset attempts after cooldown
            st.session_state['login_attempts'] = 0
    
    # If already authenticated, return True
    if st.session_state.get('password_correct', False):
        return True
        
    # Show password input
    password = st.text_input("Password", type="password", key="password_input")
    
    if password:  # Only check if password was entered
        try:
            if hmac.compare_digest(password, st.secrets["secrets"]["password"]):
                st.session_state["password_correct"] = True
                st.session_state["login_attempts"] = 0  # Reset on successful login
                log_activity("Login", True)
                st.rerun()  # Rerun to update the UI
            else:
                st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
                st.session_state["last_attempt_time"] = time.time()
                attempts_left = max(0, 5 - st.session_state["login_attempts"])
                log_activity("Login Attempt", False, reason="Incorrect password", attempts_left=attempts_left)
                if attempts_left > 0:
                    st.error(f"😕 Incorrect password. {attempts_left} attempts left.")
                else:
                    st.error("🔒 Too many failed attempts. Please try again later.")
        except Exception as e:
            log_activity("Login Error", False, error=str(e))
            st.error("An error occurred during authentication")
    
    return st.session_state.get("password_correct", False)

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Admin section for log viewing
if st.secrets.get("secrets", {}).get("admin_password"):
    if st.sidebar.checkbox("Show Admin Controls"):
        admin_pass = st.sidebar.text_input("Admin Password", type="password")
        if admin_pass == st.secrets["secrets"]["admin_password"]:
            st.sidebar.success("Admin access granted!")
            
            # Add a test log entry
            if st.sidebar.button("Add Test Log Entry"):
                logging.info("This is a test log entry from the admin panel")
                st.sidebar.success("Test log entry added!")
            
            # View logs
            if st.sidebar.button("View Logs"):
                try:
                    log_file = os.path.join('logs', 'app.log')
                    if os.path.exists(log_file):
                        with open(log_file, 'r') as f:
                            logs = f.read()
                        if not logs.strip():
                            st.sidebar.warning("Log file exists but is empty")
                            logging.info("This is a test log entry to verify logging works")
                            st.sidebar.info("Added a test log entry. Try viewing logs again.")
                        else:
                            st.sidebar.text_area("Application Logs", logs, height=300)
                    else:
                        st.sidebar.warning("Log file not found. Creating a test log entry...")
                        logging.info("Creating initial log file with this test entry")
                        st.sidebar.info("Log file created. Click 'View Logs' again to see the content.")
                except Exception as e:
                    st.sidebar.error(f"Error reading logs: {str(e)}")
                    logging.error(f"Error in log viewer: {str(e)}")

# Page title and header
st.title("OpenAI Image Editor")
st.write("Upload your images and edit them with AI")

# Add custom CSS to style the quick prompt bubbles
st.markdown("""
<style>
    /* Style the prompt bubbles */
    div[data-testid="stButton"] > button {
        border-radius: 20px;
        padding: 8px 16px;
        font-size: 0.9em;
        margin: 0px 4px 8px 0px;
        border: 1px solid rgba(49, 51, 63, 0.2);
        background-color: #f0f2f6;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #e0e2e6;
        border: 1px solid rgba(49, 51, 63, 0.4);
        color: #0F52BA;
    }
    /* Make columns tighter for the bubbles */
    div[data-testid="column"] {
        padding: 0px 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'loaded_images' not in st.session_state:
    st.session_state.loaded_images = []
if 'image_paths' not in st.session_state:
    st.session_state.image_paths = []
if 'processed_results' not in st.session_state:
    st.session_state.processed_results = []
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'processing_progress' not in st.session_state:
    st.session_state.processing_progress = 0
if 'current_image_index' not in st.session_state:
    st.session_state.current_image_index = 0

# Preset prompts for quick selection
PRESET_PROMPTS = [
    "Clear the room of all furniture",
    "Clear the room of furniture and stage as a modern living room",
    "Clear the room of furniture and stage as a modern bedroom",
    "Declutter this room",
    "Stage as a minimalist space",
    "Add modern decor"
]

# Title and introduction
st.title("OpenAI Image Editor")
st.markdown("""
    This application allows you to edit images using OpenAI's Image editing API.
    Upload your images, configure your editing prompts, and download the edited results.
""")

# Sidebar for configuration and controls
with st.sidebar:
    st.header("Configuration")
    
    # API Key input
    api_key = st.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    
    # Image resolution selection
    st.subheader("Output Resolution")
    resolution_col1, resolution_col2 = st.columns([3, 2])
    
    with resolution_col1:
        output_resolution = st.selectbox(
            "Select Resolution",
            options=["1024x1024", "1024x1536", "1536x1024", "auto"],
            index=3,
            help="Select the resolution for the edited images. Different resolutions are better for different types of images."
        )
    
    with resolution_col2:
        # Show a visual representation of the selected resolution
        if output_resolution == "1024x1024":
            st.caption("1:1 Square format (standard)")
        elif output_resolution == "1792x1024":
            st.caption("1.75:1 Landscape format (wide)")
        elif output_resolution == "1024x1792":
            st.caption("1:1.75 Portrait format (tall)")
    
    st.markdown("""<small>Note: Smaller resolutions may result in more consistent image edits, while larger resolutions offer more detail but may have artifacts.</small>""", unsafe_allow_html=True)
    
    # Note about editing
    st.info("Provide editing prompts for each image in the main panel. Each image can have its own custom editing prompt.")

    
    # File upload section
    st.subheader("Upload Images")
    uploaded_files = st.file_uploader("Choose images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    # Folder path input
    folder_path = st.text_input("Or enter a local directory path:", help="Enter the full path to a folder containing images")
    
    if st.button("Load from Directory") and folder_path:
        try:
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                # Clear previous images
                st.session_state.loaded_images = []
                st.session_state.image_paths = []
                st.session_state.processed_results = []
                st.session_state.processing_complete = False
                
                valid_extensions = ['.jpg', '.jpeg', '.png']
                loaded_count = 0
                
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in valid_extensions):
                        try:
                            img = Image.open(file_path)
                            # Convert to RGB if RGBA
                            if img.mode == 'RGBA':
                                img = img.convert('RGB')
                            
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format=img.format if img.format else 'JPEG')
                            st.session_state.loaded_images.append(img)
                            st.session_state.image_paths.append(file_path)
                            loaded_count += 1
                        except Exception as e:
                            st.warning(f"Could not load {filename}: {str(e)}")
                
                st.success(f"Loaded {loaded_count} images from directory.")
                st.rerun()
            else:
                st.error("The provided path does not exist or is not a directory.")
        except Exception as e:
            st.error(f"Error loading from directory: {str(e)}")
    
    # Process buttons
    st.subheader("Process Images")
    
    if st.button("Edit All Images"):
        if not api_key:
            st.error("Please enter your OpenAI API key.")
        elif len(st.session_state.loaded_images) == 0:
            st.error("Please upload images or load them from a directory first.")
        else:
            # Set up for processing
            st.session_state.processed_results = []
            st.session_state.processing_complete = False
            st.session_state.processing_progress = 0
            st.session_state.current_image_index = 0
            
            # Clear any previous edited images
            if 'edited_images' in st.session_state:
                st.session_state.edited_images = {}
            
            total_images = len(st.session_state.loaded_images)
            
            # Process each image
            with st.spinner(f"Editing {total_images} images..."):
                for i, img in enumerate(st.session_state.loaded_images):
                    st.session_state.current_image_index = i
                    
                    # Update progress
                    st.session_state.processing_progress = (i + 1) / total_images
                    
                    # Get image path
                    img_path = st.session_state.image_paths[i] if i < len(st.session_state.image_paths) else f"Image {i+1}"
                    
                    try:
                        # Initialize edited_images if not already present
                        if 'edited_images' not in st.session_state:
                            st.session_state.edited_images = {}
                        
                        # Get the individual prompt for this image if available
                        if 'individual_prompts' in st.session_state and i in st.session_state.individual_prompts:
                            edit_prompt = st.session_state.individual_prompts[i]
                        else:
                            edit_prompt = ""  # Empty prompt by default
                            
                        # Skip images with empty prompts
                        if not edit_prompt.strip():
                            st.warning(f"Skipping image {i+1} because it has an empty prompt.")
                            continue
                        
                        # Edit the image
                        edited_url = edit_image_with_openai(
                            api_key,
                            img,
                            edit_prompt,
                            size=output_resolution  # Pass the selected resolution
                        )
                        
                        # Store the edited image URL
                        st.session_state.edited_images[i] = edited_url
                        
                        # Add to results (placeholder text)
                        st.session_state.processed_results.append({
                            "image_path": img_path,
                            "response": f"Image edited with prompt: {edit_prompt}"
                        })
                        
                    except Exception as e:
                        error_message = f"Error processing image {i+1}: {str(e)}"
                        st.error(error_message)
                        st.session_state.processed_results.append({
                            "image_path": img_path,
                            "response": f"Error: {str(e)}"
                        })
                    
                    # Small delay to prevent rate limiting
                    time.sleep(0.5)
            
            st.session_state.processing_complete = True
            st.success("All images edited successfully!")
            st.rerun()
    
    # Export results button
    if st.session_state.processing_complete and len(st.session_state.processed_results) > 0:
        st.subheader("Export Results")
        export_format = st.selectbox("Export Format", ["JSON", "Text"], index=0)
        
        if st.button("Export Results"):
            try:
                save_path = save_results_to_file(
                    st.session_state.processed_results,
                    export_format.lower()
                )
                st.success(f"Results exported to: {save_path}")
            except Exception as e:
                st.error(f"Error exporting results: {str(e)}")

# Main area - Display loaded and processed images
if uploaded_files:
    # Clear previous images if new ones are uploaded
    if len(uploaded_files) != len(st.session_state.loaded_images):
        st.session_state.loaded_images = []
        st.session_state.image_paths = []
        st.session_state.processed_results = []
        st.session_state.processing_complete = False
    
    # Process uploaded files
    for uploaded_file in uploaded_files:
        try:
            # Read the image using PIL
            image = Image.open(uploaded_file)
            
            # Add to session state if not already present
            if uploaded_file.name not in st.session_state.image_paths:
                st.session_state.loaded_images.append(image)
                st.session_state.image_paths.append(uploaded_file.name)
        except Exception as e:
            st.error(f"Error loading image {uploaded_file.name}: {str(e)}")

# Display loaded images
if st.session_state.loaded_images:
    st.header(f"Loaded Images ({len(st.session_state.loaded_images)})")
    
    # Add 'Download All Edited Images' button if we have edited images
    if 'edited_images' in st.session_state and len(st.session_state.edited_images) > 0:
        download_col1, download_col2 = st.columns([1, 3])
        with download_col1:
            if st.button("📥 Download All Edited Images", key="download_all_button"):
                try:
                    # Create a zip file with all edited images
                    zip_path = create_zip_of_edited_images(
                        st.session_state.edited_images,
                        st.session_state.loaded_images,
                        st.session_state.image_paths
                    )
                    
                    if zip_path and os.path.exists(zip_path):
                        # Read the zip file and create a download link
                        with open(zip_path, "rb") as f:
                            bytes_data = f.read()
                        
                        b64_zip = base64.b64encode(bytes_data).decode()
                        href = f'<a href="data:application/zip;base64,{b64_zip}" download="edited_images.zip">Download ZIP file</a>'
                        
                        with download_col2:
                            st.markdown(href, unsafe_allow_html=True)
                            st.success(f"Created a ZIP file with {len(st.session_state.edited_images)} edited images!")
                    else:
                        st.error("Failed to create ZIP file. Please try again.")
                except Exception as e:
                    st.error(f"Error creating download: {str(e)}")
    
    # Show a progress bar during processing
    if not st.session_state.processing_complete and st.session_state.processing_progress > 0:
        st.progress(st.session_state.processing_progress)
        st.caption(f"Processing image {st.session_state.current_image_index + 1} of {len(st.session_state.loaded_images)}")
    
    # Initialize individual prompts in session state if they don't exist
    if 'individual_prompts' not in st.session_state:
        st.session_state.individual_prompts = {}
    
    # Display images with individual prompt fields in a vertical layout
    for i, image in enumerate(st.session_state.loaded_images):
        # Create a container for each image with a border
        with st.container():
            st.markdown("---")  # Horizontal separator
            
            # Get image caption
            image_caption = st.session_state.image_paths[i] if i < len(st.session_state.image_paths) else f"Image {i+1}"
            st.subheader(f"Image {i+1}: {image_caption}")
            
            # Create two columns - one for the image(s) and one for the prompt
            img_col, prompt_col = st.columns([2, 3])
            
            with img_col:
                # If edited image is available, show it alongside the original
                if 'edited_images' in st.session_state and i in st.session_state.edited_images:
                    try:
                        image_result = st.session_state.edited_images[i]
                        
                        # Different handling based on if it's a URL or a file path
                        if isinstance(image_result, str) and image_result.startswith(('http://', 'https://')):
                            # It's a URL, download the image
                            response = requests.get(image_result)
                            edited_image = Image.open(io.BytesIO(response.content))
                        else:
                            # It's a local file path
                            edited_image = Image.open(image_result)
                        
                        # Create two rows - one for each image
                        st.image(image, caption="Original")
                        st.image(edited_image, caption="Edited")
                        
                        # Create download button for edited image
                        buffered = io.BytesIO()
                        edited_image.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        href = f'<a href="data:image/png;base64,{img_str}" download="edited_image_{i}.png">Download Edited Image</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error displaying edited image: {str(e)}")
                        st.image(image, caption=image_caption)
                else:
                    # Show original image if no edited version
                    st.image(image, caption=image_caption)
            
            with prompt_col:
                # Get the default prompt value from session state or use an empty string
                default_prompt = st.session_state.individual_prompts.get(i, "")
                
                # Create individual prompt field for this image
                prompt_value = st.text_area(
                    f"Edit prompt for this image",
                    value=default_prompt,
                    key=f"individual_prompt_{i}",
                    height=150
                )
                
                # Store the prompt value in session state
                st.session_state.individual_prompts[i] = prompt_value
                
                # Create clickable prompt bubbles
                st.write("**Quick Prompts:**")
                
                # Helper function to handle prompt updates
                def add_preset_to_prompt(preset_text, image_index):
                    # Get current prompt from the stored prompts
                    current_prompt = st.session_state.individual_prompts.get(image_index, "")
                    # Add a space between existing text and new preset if needed
                    if current_prompt and not current_prompt.endswith(" "):
                        current_prompt += " "
                    # Update the individual prompts dictionary
                    st.session_state.individual_prompts[image_index] = current_prompt + preset_text
                    # This will trigger a rerun and update the text area
                    st.rerun()
                
                # Create a row of buttons for each preset prompt
                cols = st.columns(3)
                for j, preset in enumerate(PRESET_PROMPTS):
                    col_index = j % 3
                    with cols[col_index]:
                        button_key = f"preset_{i}_{j}"
                        # Create a button that calls a function to update the session state
                        if st.button(preset, key=button_key, type="secondary"):
                            add_preset_to_prompt(preset, i)
                
                # Add edit button for this specific image
                if st.button(f"Edit this image", key=f"edit_button_{i}"):
                    with st.spinner(f"Editing image {i+1}..."):
                        try:
                            # Get the prompt for this image
                            edit_prompt = st.session_state.individual_prompts[i]
                            
                            # Check for empty prompt
                            if not edit_prompt.strip():
                                st.warning("Please enter a prompt or click some quick prompts before editing.")
                                continue
                            
                            # Call the edit function
                            edited_image_url = edit_image_with_openai(
                                api_key, 
                                image, 
                                edit_prompt,
                                size=output_resolution  # Pass the selected resolution
                            )
                            
                            # Store the URL in session state
                            if 'edited_images' not in st.session_state:
                                st.session_state.edited_images = {}
                            
                            # Update the edited image result
                            st.session_state.edited_images[i] = edited_image_url
                            
                            # Add to processed results if not already there
                            if not st.session_state.processing_complete or i >= len(st.session_state.processed_results):
                                if len(st.session_state.processed_results) <= i:
                                    # Extend the results list if needed
                                    st.session_state.processed_results.extend(
                                        [{"image_path": "" , "response": ""}] * (i + 1 - len(st.session_state.processed_results))
                                    )
                                
                                # Update the results
                                st.session_state.processed_results[i] = {
                                    "image_path": image_caption,
                                    "response": f"Image edited with prompt: {edit_prompt}"
                                }
                            
                            st.success(f"Image {i+1} edited successfully!")
                            st.rerun()  # Refresh to show the edited image
                        except Exception as e:
                            st.error(f"Error editing image {i+1}: {str(e)}")
                
                # Show edit prompt if available
                if st.session_state.processing_complete and i < len(st.session_state.processed_results):
                    with st.expander("View Edit Prompt"):
                        prompt_used = st.session_state.individual_prompts.get(i, '')
                        if prompt_used:
                            st.markdown(f"**Edit prompt used:** {prompt_used}")
                        else:
                            st.markdown("*No prompt was used for this image.*")


# Display a summary of edited images
if st.session_state.processing_complete and 'edited_images' in st.session_state and len(st.session_state.edited_images) > 0:
    st.header(f"Edited Images Summary ({len(st.session_state.edited_images)} images)")
    st.success("All images have been edited successfully! You can download each image individually or use the 'Download All Edited Images' button at the top.")

else:
    if not st.session_state.loaded_images:
        st.info("Please upload images or load them from a directory to begin.")
