import os

from groq import Groq
from groq import RateLimitError as GroqRateLimitError


class GroqClient:
    def __init__(self, model: str | None = None):
        self._client = Groq(api_key=os.environ["GROQ_API_KEY"])
        self._model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    @property
    def model_name(self) -> str:
        return self._model

    def answer(self, question: str, context: str, domain_prompt: str) -> str:
        if context:
            user_content = (
                "You have been provided with relevant document excerpts below. "
                "Read them carefully and provide a thorough, well-structured answer.\n\n"
                "=== RETRIEVED DOCUMENT EXCERPTS ===\n"
                f"{context}\n"
                "=== END OF DOCUMENTS ===\n\n"
                f"Question: {question}\n\n"
                "Instructions for your response:\n"
                "- Begin with a direct, clear answer to the question.\n"
                "- Use ## and ### markdown headers to organize sections.\n"
                "- Use bullet points (-) or numbered lists (1. 2. 3.) for structured information.\n"
                "- Cite sources as [1], [2], etc. where information comes from specific documents.\n"
                "- Be comprehensive — cover all relevant aspects found in the documents.\n"
                "- End with a brief **Summary** or **Key Takeaways** section if the answer is complex.\n"
                "- Write in a professional, expert tone."
            )
        else:
            user_content = (
                "No documents are currently indexed in the knowledge base.\n\n"
                f"Question: {question}\n\n"
                "Please answer based on your general knowledge. "
                "Clearly note at the start that no documents were found in the knowledge base, "
                "then provide the most helpful response you can with proper structure and formatting."
            )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": domain_prompt},
                    {"role": "user", "content": user_content},
                ],
                # Stage 2: 0.0 rather than the original 0.3 -- answer
                # caching requires deterministic generation, and this is
                # the only answer-generation call site today.
                temperature=0.0,
                max_tokens=4096,
            )
            return response.choices[0].message.content or ""
        except GroqRateLimitError as exc:
            raise RuntimeError(
                "Groq API rate limit reached. The daily token quota (100,000 tokens/day on the free tier) "
                "has been exhausted. Please wait until midnight UTC for the limit to reset, or upgrade your "
                "Groq plan at https://console.groq.com/settings/billing"
            ) from exc
