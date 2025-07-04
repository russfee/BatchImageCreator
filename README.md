# OpenAI Image Editor

A powerful Streamlit-based application for batch processing and editing images using OpenAI's GPT Image-1 model. This tool allows you to transform interior photos with precise AI-powered editing capabilities, customizable prompt management, and advanced configuration options.

![OpenAI Image Editor](attached_assets/Screenshot%202025-05-03%20at%2010.51.54%20AM.png)

## 🚀 Quick Start

1. **Launch the app** (requires Python 3.6+):
   ```bash
   streamlit run app.py
   ```

2. **Access the app** in your browser at `http://localhost:8501`

3. **Enter the password** when prompted

4. **Start editing images** with AI-powered transformations

For detailed setup and advanced usage, see the sections below.

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

### Local Development

1. Clone this repository:
```bash
git clone https://github.com/yourusername/openai-image-editor.git
cd openai-image-editor
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file

5. Run the application locally:
```bash
streamlit run app.py
```

The application will be available at http://localhost:8501

## Deployment

### Option 1: Streamlit Cloud (Recommended)

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign in with your GitHub account
3. Click "New app" and select your repository
4. Set the following configuration:
   - Branch: `main` (or your preferred branch)
   - Main file path: `app.py`
   - Python version: 3.8 or higher
5. Add your OpenAI API key as a secret in the "Advanced settings" section:
   - Click "Advanced settings..."
   - Add a new secret: `OPENAI_API_KEY` with your API key as the value
6. Click "Deploy!"

### Option 2: Hugging Face Spaces (Free with GPU)

1. Create an account on [Hugging Face](https://huggingface.co/)
2. Create a new Space and select "Streamlit" as the SDK
3. Push your code to the Space's repository
4. Add your OpenAI API key in the Space's settings:
   - Go to Settings → Repository secrets
   - Add a new secret: `OPENAI_API_KEY` with your API key as the value

### Option 3: Docker Deployment

1. Create a `Dockerfile` in your project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. Build and run the Docker container:
```bash
docker build -t batch-image-creator .
docker run -p 8501:8501 -e OPENAI_API_KEY=your_api_key_here batch-image-creator
```

3. Deploy the container to your preferred cloud provider (AWS ECS, Google Cloud Run, etc.)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key_here
```

Or set them in your deployment platform's environment settings.

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

- **Auto** (Recommended) - Automatically selects the best resolution based on the input image's aspect ratio
- **Square format** (1024x1024) - Perfect square format for balanced images
- **Portrait format** (1024x1536) - Taller format for portrait-oriented images
- **Landscape format** (1536x1024) - Wider format for landscape-oriented images

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