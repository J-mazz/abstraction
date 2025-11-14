#!/usr/bin/env python3
"""
Script to download the Mixtral-8x7B model before running the application.
This is useful to avoid waiting during the first launch.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.model_loader import ModelLoader
from loguru import logger


def main():
    """Download the model."""
    # Load environment
    load_dotenv()

    # Get token
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        logger.error("HUGGINGFACE_TOKEN not found in .env file!")
        logger.error("Please add your HuggingFace token to .env")
        sys.exit(1)

    # Get model name and cache dir
    model_name = os.getenv("MODEL_NAME", "mistral-7b-instruct-v0.3")
    cache_dir = os.getenv("MODEL_CACHE_DIR", "./models")

    logger.info("=" * 60)
    logger.info("Model Downloader")
    logger.info("=" * 60)
    logger.info(f"Model: {model_name}")
    logger.info(f"Cache directory: {cache_dir}")
    logger.info("")

    # Estimate size based on model
    if "mixtral" in model_name.lower():
        logger.info("This will download approximately 47GB of data.")
        logger.info("With 4-bit quantization, it will use ~26GB of memory at runtime.")
        logger.info("NOTE: Requires 32GB+ RAM!")
    else:
        logger.info("This will download approximately 14GB of data.")
        logger.info("With 4-bit quantization, it will use ~3.5GB of memory at runtime.")
        logger.info("Works with 16GB RAM.")
    logger.info("")

    # Confirm
    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        logger.info("Download cancelled.")
        sys.exit(0)

    # Create model loader
    logger.info("Initializing model loader...")
    loader = ModelLoader(
        model_name=model_name,
        cache_dir=cache_dir,
        load_in_4bit=True
    )

    # Authenticate
    logger.info("Authenticating with HuggingFace...")
    loader.authenticate(hf_token)

    # Load model (this downloads it)
    logger.info("Downloading model (this may take 10-30 minutes)...")
    logger.info("Please be patient...")

    try:
        loader.load_model()
        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ Model downloaded successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info(f"Model info: {loader.get_model_info()}")
        logger.info("")
        logger.info("You can now run the application with: python3 src/main.py")

    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        logger.error("")
        logger.error("Common issues:")
        logger.error("1. Invalid HuggingFace token")
        logger.error("2. Insufficient disk space (need ~20GB for Mistral-7B)")
        logger.error("3. Network connection issues")
        logger.error("4. Out of memory (use mistral-7b for 16GB RAM systems)")
        sys.exit(1)


if __name__ == "__main__":
    main()
