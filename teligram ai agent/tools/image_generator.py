import requests
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class ImageGeneratorTool:
    """
    Generates high-quality AI images using Pollinations.ai (free, no API key needed).
    Returns image bytes ready to send via Telegram.
    """
    BASE_URL = "https://image.pollinations.ai/prompt/"

    @staticmethod
    def generate_image(prompt: str, width: int = 1024, height: int = 1024, model: str = "flux") -> bytes:
        """
        Generates an image from a text prompt.
        Models: 'flux' (best quality), 'turbo' (faster)
        """
        try:
            enhanced_prompt = f"{prompt}, ultra high quality, 8k, photorealistic, stunning"
            encoded = urllib.parse.quote(enhanced_prompt)
            url = (
                f"{ImageGeneratorTool.BASE_URL}{encoded}"
                f"?width={width}&height={height}&model={model}&nologo=true&enhance=true&safe=false"
            )
            logger.info(f"Generating image with prompt: {prompt[:60]}...")
            response = requests.get(url, timeout=90)
            if response.status_code == 200 and response.content:
                return response.content
            logger.error(f"Image generation failed: HTTP {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None

    @staticmethod
    def generate_image_for_telegram(prompt: str) -> bytes:
        """Wrapper that tries flux first, then turbo as fallback."""
        img = ImageGeneratorTool.generate_image(prompt, width=1024, height=1024, model="flux")
        if not img:
            img = ImageGeneratorTool.generate_image(prompt, width=1024, height=1024, model="turbo")
        return img
