"""
Model loader for Mistral with HuggingFace Transformers.
Uses Apache 2.0 licensed Mistral-7B-Instruct-v0.3 model.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline
)
from huggingface_hub import login, hf_hub_download
from loguru import logger


class ModelLoader:
    """Handles loading and managing the Mistral model."""

    # Apache 2.0 licensed models only
    SUPPORTED_MODELS = {
        "mistral-7b-instruct-v0.3": "mistralai/Mistral-7B-Instruct-v0.3",  # ~14GB, 3.5GB with 4-bit (Recommended for 16GB RAM)
        "mistral-7b-v0.1": "mistralai/Mistral-7B-v0.1",  # ~14GB, 3.5GB with 4-bit
        "mixtral-8x7b-instruct": "mistralai/Mixtral-8x7B-Instruct-v0.1",  # ~47GB, 26GB with 4-bit (Requires 32GB+ RAM)
    }

    def __init__(
        self,
        model_name: str = "mistral-7b-instruct-v0.3",
        cache_dir: str = "./models",
        load_in_4bit: bool = True,
        device: str = "auto"
    ):
        """
        Initialize the model loader.

        Args:
            model_name: Name of the model to load (must be Apache 2.0 licensed)
            cache_dir: Directory to cache the model
            load_in_4bit: Whether to use 4-bit quantization (reduces memory to ~3.5GB for 7B models)
            device: Device to load model on ('auto', 'cuda', 'cpu')
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.load_in_4bit = load_in_4bit
        self.device = device

        self.model = None
        self.tokenizer = None
        self.pipeline = None

        # Get full model path
        if model_name in self.SUPPORTED_MODELS:
            self.model_path = self.SUPPORTED_MODELS[model_name]
            logger.info(f"Using Apache 2.0 licensed model: {self.model_path}")
        else:
            logger.warning(f"Unknown model {model_name}, using as-is. Ensure it's Apache 2.0 licensed!")
            self.model_path = model_name

    def authenticate(self, token: Optional[str] = None) -> None:
        """
        Authenticate with HuggingFace Hub.

        Args:
            token: HuggingFace API token (uses env var HUGGINGFACE_TOKEN if None)
        """
        hf_token = token or os.getenv("HUGGINGFACE_TOKEN")
        if hf_token:
            try:
                login(token=hf_token)
                logger.info("Successfully authenticated with HuggingFace Hub")
            except Exception as e:
                logger.error(f"Failed to authenticate with HuggingFace: {e}")
        else:
            logger.warning("No HuggingFace token provided. Some models may not be accessible.")

    def load_model(self) -> None:
        """Load the model and tokenizer."""
        try:
            logger.info(f"Loading model: {self.model_path}")

            # Configure quantization if enabled
            quantization_config = None
            if self.load_in_4bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True
                )
                logger.info("Using 4-bit quantization to reduce memory usage")

            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                cache_dir=str(self.cache_dir),
                trust_remote_code=True
            )

            # Ensure pad token is set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model
            logger.info("Loading model weights (this may take a while)...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                cache_dir=str(self.cache_dir),
                quantization_config=quantization_config,
                device_map=self.device,
                trust_remote_code=True,
                torch_dtype=torch.float16 if not self.load_in_4bit else None
            )

            # Create text generation pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map=self.device
            )

            logger.info("Model loaded successfully!")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        do_sample: bool = True,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        if self.pipeline is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Format prompt for instruction models
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"

            outputs = self.pipeline(
                formatted_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                return_full_text=False,
                **kwargs
            )

            return outputs[0]['generated_text'].strip()

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if self.model is None:
            return {"status": "not_loaded"}

        return {
            "status": "loaded",
            "model_name": self.model_name,
            "model_path": self.model_path,
            "license": "Apache 2.0",
            "quantization": "4-bit" if self.load_in_4bit else "fp16",
            "device": str(self.model.device) if hasattr(self.model, 'device') else "unknown",
            "parameters": sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        }

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            del self.tokenizer
            del self.pipeline
            self.model = None
            self.tokenizer = None
            self.pipeline = None
            torch.cuda.empty_cache()
            logger.info("Model unloaded and memory cleared")


def download_model(
    model_name: str = "mistral-7b-instruct-v0.3",
    cache_dir: str = "./models",
    hf_token: Optional[str] = None
) -> Path:
    """
    Download a Mistral model from HuggingFace Hub.

    Args:
        model_name: Name of the model to download
        cache_dir: Directory to save the model
        hf_token: HuggingFace API token

    Returns:
        Path to the downloaded model
    """
    loader = ModelLoader(model_name=model_name, cache_dir=cache_dir)
    loader.authenticate(hf_token)
    loader.load_model()
    logger.info(f"Model downloaded and cached at: {cache_dir}")
    return Path(cache_dir)
