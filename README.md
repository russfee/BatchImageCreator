# OpenAI Image Editor

A powerful Streamlit-based application for batch processing and editing images using OpenAI's GPT Image-1 model. This tool allows you to transform interior photos with precise AI-powered editing capabilities, customizable prompt management, and advanced configuration options.

![OpenAI Image Editor](attached_assets/Screenshot%202025-05-03%20at%2010.51.54%20AM.png)

## Features

### Image Handling
- **Batch Processing**: Upload multiple images at once through the UI or load from a local directory
- **Individual Editing**: Edit each image with custom prompts specific to that image
- **Bulk Editing**: Process all images at once with individual prompts
- **Resolution Control**: Choose from three output resolution options (square, landscape, portrait)

### Prompt Management
- **Quick Prompt Bubbles**: Click on preset prompts to quickly build editing instructions
- **Prompt Combination**: Stack multiple quick prompts to create detailed editing instructions
- **Custom Prompts**: Fully customize editing instructions for each image
- **Empty Prompt Handling**: Intelligent detection and skipping of images with empty prompts

### Result Handling
- **Side-by-Side Comparison**: View original and edited images together
- **Individual Downloads**: Download any single edited image
- **Batch Downloads**: Create and download a ZIP file with all edited images
- **Export Results**: Save processing details in JSON or text format

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/openai-image-editor.git
cd openai-image-editor
```

2. Install the required packages:
```bash
pip install openai pillow streamlit zipfile36
```

3. Set up your OpenAI API key as an environment variable (optional):
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Access the application in your web browser at http://localhost:5000

3. Upload images through the sidebar interface or load from a local directory

4. For each image:
   - Create an editing prompt or use the quick prompts
   - Click "Edit This Image" to process individually, or
   - Use "Edit All Images" to process all images at once

5. View results and download edited images individually or in bulk

## Available Quick Prompts

The application comes with several preset prompts specifically designed for interior photo editing:

- Clear the room of all furniture
- Clear the room of furniture and stage as a modern living room
- Clear the room of furniture and stage as a modern bedroom
- Declutter this room
- Stage as a minimalist space
- Add modern decor

## Resolution Options

Control the output image size by selecting one of these resolution options:

- **Square format** (1024x1024) - Standard option with balanced dimensions
- **Landscape format** (1792x1024) - Better for wide scenes and rooms
- **Portrait format** (1024x1792) - Better for tall images or vertical spaces

## Requirements

- Python 3.6+
- OpenAI API key with access to the GPT Image-1 model
- Internet connection for API access
- Streamlit 1.10+
- Pillow (PIL)
- zipfile36

## Technical Details

This application uses:
- **OpenAI GPT Image-1**: Advanced AI model for image editing (transformation, manipulation)
- **Streamlit**: Python framework for creating interactive web applications
- **PIL/Pillow**: Python Imaging Library for image processing
- **Base64 encoding**: For image transfer and display within the browser
- **ZIP file creation**: For batch downloads

## Notes

- The OpenAI API key can be entered directly in the application or set as an environment variable
- Large images are automatically processed to meet the size requirements of OpenAI's API
- The application stores temporary images in your system's temporary directory
- For best results, provide clear and specific editing instructions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT Image-1 model API
- Streamlit team for their excellent framework