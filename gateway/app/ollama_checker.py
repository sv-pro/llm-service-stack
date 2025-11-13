"""Ollama health checking and validation utilities."""

import httpx
import asyncio
from typing import List, Dict, Optional, Tuple
from .config import settings


class OllamaChecker:
    """Checks Ollama installation and available models."""

    def __init__(self):
        self.base_url = settings.OLLAMA_API_BASE
        self.required_models = self._parse_required_models()
        self.available = False
        self.installed_models: List[str] = []

    def _parse_required_models(self) -> List[str]:
        """Parse comma-separated required models from config."""
        if not settings.OLLAMA_CHECK_MODELS:
            return []
        return [m.strip() for m in settings.OLLAMA_CHECK_MODELS.split(",") if m.strip()]

    async def check_ollama_available(self) -> bool:
        """Check if Ollama is installed and accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    async def get_installed_models(self) -> List[str]:
        """Get list of installed Ollama models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    # Ollama returns models in 'models' array
                    models = data.get("models", [])
                    return [model.get("name", "").split(":")[0] for model in models]
                return []
        except (httpx.RequestError, httpx.TimeoutException):
            return []

    async def check_model_installed(self, model_name: str) -> bool:
        """Check if a specific model is installed."""
        models = await self.get_installed_models()
        # Check both exact match and base name (without tag)
        base_name = model_name.split(":")[0]
        return base_name in models or model_name in models

    async def check_all(self) -> Tuple[bool, Dict[str, any]]:
        """
        Perform comprehensive Ollama health check.

        Returns:
            Tuple of (success, details_dict)
        """
        result = {
            "ollama_available": False,
            "ollama_url": self.base_url,
            "installed_models": [],
            "required_models": self.required_models,
            "missing_models": [],
            "status": "unknown"
        }

        # Check if Ollama is available
        self.available = await self.check_ollama_available()
        result["ollama_available"] = self.available

        if not self.available:
            result["status"] = "unavailable"
            result["message"] = f"Ollama is not accessible at {self.base_url}"
            return False, result

        # Get installed models
        self.installed_models = await self.get_installed_models()
        result["installed_models"] = self.installed_models

        # Check required models if specified
        if self.required_models:
            missing = []
            for required in self.required_models:
                if not await self.check_model_installed(required):
                    missing.append(required)

            result["missing_models"] = missing

            if missing:
                result["status"] = "missing_models"
                result["message"] = f"Ollama is running but missing required models: {', '.join(missing)}"
                return False, result

        result["status"] = "ready"
        result["message"] = "Ollama is ready with all required models"
        return True, result

    def get_suggested_commands(self, missing_models: List[str]) -> List[str]:
        """Get suggested commands to install missing models."""
        return [f"ollama pull {model}" for model in missing_models]

    def format_status_message(self, details: Dict[str, any]) -> str:
        """Format a human-readable status message."""
        lines = []
        lines.append("=" * 60)
        lines.append("Ollama Status Check")
        lines.append("=" * 60)

        if not details["ollama_available"]:
            lines.append(f"❌ Ollama NOT accessible at {details['ollama_url']}")
            lines.append("")
            lines.append("To install Ollama:")
            lines.append("  • Visit: https://ollama.ai")
            lines.append("  • Or run: curl https://ollama.ai/install.sh | sh")
            lines.append("")
            lines.append("After installation, start Ollama:")
            lines.append("  • ollama serve")
        else:
            lines.append(f"✅ Ollama is running at {details['ollama_url']}")
            lines.append(f"📦 Installed models: {len(details['installed_models'])}")

            if details['installed_models']:
                for model in details['installed_models']:
                    lines.append(f"   • {model}")

            if details['required_models']:
                lines.append("")
                lines.append(f"🔍 Required models: {', '.join(details['required_models'])}")

                if details['missing_models']:
                    lines.append("")
                    lines.append(f"❌ Missing models: {', '.join(details['missing_models'])}")
                    lines.append("")
                    lines.append("To install missing models, run:")
                    for cmd in self.get_suggested_commands(details['missing_models']):
                        lines.append(f"  • {cmd}")
                else:
                    lines.append("✅ All required models are installed")

        lines.append("=" * 60)
        return "\n".join(lines)


# Global instance
ollama_checker = OllamaChecker()


async def check_ollama_on_startup() -> None:
    """Check Ollama availability on startup and log results."""
    if not settings.OLLAMA_ENABLED:
        print("ℹ️  Ollama checking disabled (OLLAMA_ENABLED=false)")
        return

    print("\n🔍 Checking Ollama availability...")
    success, details = await ollama_checker.check_all()

    # Print formatted status
    print(ollama_checker.format_status_message(details))

    # Don't fail startup if Ollama is unavailable (it's optional)
    # But warn if required models are specified and missing
    if not success and ollama_checker.required_models:
        print("\n⚠️  Warning: Ollama models are missing, but continuing startup...")
        print("    LiteLLM will use other providers (OpenAI, Anthropic, etc.)")

    print("")  # Empty line for readability
