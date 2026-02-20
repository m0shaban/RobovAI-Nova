import logging
from backend.core.llm import llm_client

logger = logging.getLogger(__name__)

async def generate_smart_content(original_content: str, persona: str) -> str:
    """
    Rewrites the fetched content using the selected AI Persona via the LLMClient.
    """
    system_prompt = (
        f"You are an expert AI content creator and marketer. "
        f"Your specific persona is: '{persona}'. "
        f"Rewrite the provided news/content into an engaging, high-quality post suitable for your persona. "
        f"Use appropriate emojis, tone, and formatting (like bullet points or bold text if helpful). "
        f"Respond in Arabic."
    )
    
    prompt = f"Original Content:\n{original_content}\n\nPlease rewrite this:"
    
    try:
        logger.info(f"Generating content with persona: {persona}")
        generated_text = await llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            provider="auto" # Will try Groq, then fallback to others
        )
        return generated_text
    except Exception as e:
        logger.error(f"Error generating smart content: {e}")
        return ""
