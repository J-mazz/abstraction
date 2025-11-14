# Quick Start Guide

Get up and running with Abstraction in 5 minutes!

## Prerequisites

- **Python 3.10 or higher**
- **20GB free disk space** (for Mistral-7B model)
- **16GB RAM** (model uses ~3.5GB with 4-bit quantization)
- **GPU optional** (works fine on CPU or integrated graphics, just slower)

## Installation

### 1. Set up your HuggingFace Token

1. Go to https://huggingface.co/settings/tokens
2. Create a new token (read access is sufficient)
3. Copy the token

### 2. Configure the Application

```bash
# Create .env file
cp .env.example .env

# Edit .env and paste your token
nano .env  # or use any text editor
```

Your `.env` should look like:
```env
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MODEL_NAME=mistral-7b-instruct-v0.3
MODEL_CACHE_DIR=./models
```

**Note**: Default is Mistral-7B (works with 16GB RAM). If you have 32GB+ RAM, you can use `mixtral-8x7b-instruct` for more powerful responses.

### 3. Run the Application

#### Option A: Using the Quick Start Script (Linux/macOS)

```bash
./run.sh
```

This script will:
- Create a virtual environment
- Install dependencies
- Launch the application

#### Option B: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 src/main.py
```

### 4. Wait for Model Download

On first run, the Mistral-7B model (~14GB) will be downloaded automatically.

- **Download time**: 5-15 minutes (depending on internet speed)
- **Progress**: Check terminal for download progress
- **Location**: Models are cached in `./models/` directory

**Tip**: You can pre-download the model to avoid waiting at launch:
```bash
python3 download_model.py
```

### 5. Start Using the Agent!

Once the GUI appears:

1. **Type a task** in the input field
2. **Click Send** or press Enter
3. **Approve tools** when the dialog appears
4. **View results** in the chat window

## Example Tasks to Try

### Coding
```
Read this code and format it:
def foo(x,y):
    return x+y
```

### Web
```
What's the current time from worldtimeapi.org?
```

### Accounting
```
Calculate invoice total for 3 items at $50 each with 8% tax
```

### Writing
```
Count words in this text: The quick brown fox jumps over the lazy dog
```

## Troubleshooting

### "HUGGINGFACE_TOKEN not found"
- Make sure you created `.env` file
- Check that the token is correct
- Ensure no extra spaces in the token

### "Out of memory" during model loading
- Ensure you're using Mistral-7B (default) not Mixtral-8x7B
- Enable 4-bit quantization (default, should already be on)
- Close other applications
- Check `.env` - should say `MODEL_NAME=mistral-7b-instruct-v0.3`

### GUI doesn't appear
```bash
# Linux: Install Qt dependencies
sudo apt install libxcb-xinerama0 libxcb-cursor0

# Verify PySide6
python3 -c "from PySide6.QtWidgets import QApplication"
```

### Slow inference on CPU/integrated graphics
- **This is normal!** CPU inference is slower than GPU
- **Mistral-7B on CPU**: 5-10 tokens/sec is expected
- **Integrated graphics**: 3-8 tokens/sec is normal
- For faster speeds, use a dedicated GPU
- Responses typically take 10-30 seconds to complete

## Next Steps

- Read the full [README.md](README.md) for advanced features
- Check out [config/config.yaml](config/config.yaml) for customization
- Add your own tools (see README.md Development section)
- Build a standalone executable with PyApp (see BUILD_PYAPP.md)

## Getting Help

- Check logs in `./logs/` directory
- Set `LOG_LEVEL=DEBUG` in `.env` for more details
- Open an issue on GitHub

---

**Enjoy building with Abstraction! 🚀**
