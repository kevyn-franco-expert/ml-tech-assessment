import asyncio
import logging
from typing import Type

import openai
import pydantic

from app.domain.errors import LLMServiceError, LLMTimeoutError, LLMRateLimitError
from app.domain.ports import LLm

logger = logging.getLogger(__name__)


class OpenAIAdapterImpl(LLm):
    def __init__(self, api_key: str, model: str, timeout: float = 30.0):
        self._model = model
        self._timeout = timeout
        self._client = openai.OpenAI(api_key=api_key)
        self._aclient = openai.AsyncOpenAI(api_key=api_key)

    def run_completion(self, system_prompt: str, user_prompt: str, dto: Type[pydantic.BaseModel]) -> pydantic.BaseModel:
        try:
            completion = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=dto,
                timeout=self._timeout
            )
            return completion.choices[0].message.parsed
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise LLMRateLimitError()
        except openai.APITimeoutError as e:
            logger.error(f"OpenAI request timed out: {e}")
            raise LLMTimeoutError()
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI completion: {e}")
            raise LLMServiceError(f"Unexpected error: {str(e)}")

    async def run_completion_async(self, system_prompt: str, user_prompt: str, dto: Type[pydantic.BaseModel]) -> pydantic.BaseModel:
        try:
            completion = await asyncio.wait_for(
                self._aclient.beta.chat.completions.parse(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format=dto
                ),
                timeout=self._timeout
            )
            return completion.choices[0].message.parsed
        except asyncio.TimeoutError:
            logger.error("OpenAI request timed out")
            raise LLMTimeoutError()
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise LLMRateLimitError()
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI completion: {e}")
            raise LLMServiceError(f"Unexpected error: {str(e)}")