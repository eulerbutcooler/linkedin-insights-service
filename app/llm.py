from google import genai
from google.genai import types
from app.core.logging import get_logger

logger=get_logger(__name__)

class LLMClient:

    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-lite"):
        self._client=genai.Client(api_key=api_key)
        self._model=model

    async def summarize(self, sys_prompt:str, usr_prompt:str)->str:
        try:
            resp=await self._client.aio.models.generate_content(
                model=self._model,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=usr_prompt)])],
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    temperature=0.4,
                    max_output_tokens=512,
                )
            )
            return (resp.text or "").strip()
        except Exception as exc:
            logger.error("llm.call_failed", error=str(exc))
            raise
