import asyncio
import json
import random
import string
from typing import Iterator, Optional
import openai
import aiohttp
import requests
from .ai_types import ChatCompletionChoice, ChatCompletionChunk, ChatCompletionChunkChoice, ChatCompletionChunkDelta, ChatCompletionMessage, ChatCompletion, CompletionUsage, Model

class GPT():
    def __init__(self, TOKEN: str, url: Optional[str] = None) -> None:
        openai.api_key = TOKEN
        if url is not None:
            openai.api_base = url
    
    async def acreate_chat_completion(
        self,
        messages: list[ChatCompletionMessage],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.9,
        max_tokens: int = -1,
        top_p: float = 1,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
        n: int = 1,
        stream: bool = False
    ) -> Iterator[ChatCompletionChunk] | ChatCompletion:
        return await openai.ChatCompletion.acreate(
            messages = messages,
            model = model,
            temperature = temperature,
            max_tokens = max_tokens,
            top_p = top_p,
            frequency_penalty = frequency_penalty,
            presence_penalty = presence_penalty,
            n = n,
            stream = stream
        ) # type: ignore
        

    def create_chat_completion(
        self,
        messages: list[ChatCompletionMessage],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.9, 
        max_tokens: int = -1, 
        top_p: float = 1, 
        frequency_penalty: float = 0, 
        presence_penalty: float = 0,
        n: int = 1,
        stream: bool = False
    ) -> Iterator[ChatCompletionChunk] | ChatCompletion:
        return openai.ChatCompletion.create(
            messages = messages,
            model = model,
            temperature = temperature,
            max_tokens = max_tokens,
            top_p = top_p,
            frequency_penalty = frequency_penalty,
            presence_penalty = presence_penalty,
            n = n,
            stream = stream
        ) # type: ignore

class LocalLlama():
    def __init__(self, TOKEN: str, url: str = "http://localhost:8000") -> None:
        self.url = url
        try:
            res = requests.get(self.url + "/docs")
            print(res)
        except Exception as e:
            print("Failed to connect to local llama server")
            print(e)

    async def acreate_chat_completion(
        self,
        messages: list[ChatCompletionMessage],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.9, 
        max_tokens: int = -1, 
        top_p: float = 1, 
        frequency_penalty: float = 0, 
        presence_penalty: float = 0,
        n: int = 1,
        stream: bool = False
    ) -> ChatCompletion:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url + "/v1/chat/completions",
                json={
                    "messages": messages,
                    "max_tokens": max(max_tokens, 2048),
                }
            ) as resp:
                return await resp.json()
    
    # Chat completion using the acreate_chat_completion method
    def create_chat_completion(
        self,
        messages: list[ChatCompletionMessage],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.9, 
        max_tokens: int = -1, 
        top_p: float = 1, 
        frequency_penalty: float = 0, 
        presence_penalty: float = 0,
        n: int = 1,
        stream: bool = False
    ) -> ChatCompletion:
        return asyncio.get_event_loop().run_until_complete(asyncio.create_task(self.acreate_chat_completion(messages)))

class DummyLlm():
    def __init__(self, TOKEN: str) -> None:
        pass

    @staticmethod
    def __random_word(n: Optional[int] = None):
        if n is None:
            n = random.randint(2, 12)
        return "".join(random.choice(string.ascii_letters) for i in range(n))
    
    @staticmethod
    def __random_sentence(n: Optional[int] = None) -> str:
        if n is None:
            n = random.randint(2, 12)
        return " ".join(DummyLlm.__random_word() for i in range(n))

    def __dummy_stream(
        self,
        messages: list[ChatCompletionMessage],
        model: str = "gpt-3.5-turbo",
        max_tokens: int = -1,
    ):
        r = random.randint(1, max(max_tokens, 1))
        for i in range(r):
            yield ChatCompletionChunk(
                id = "dummy", 
                model=model, 
                object="chat.completion.chunk", 
                created=0, 
                choices=[
                    ChatCompletionChunkChoice(
                        index=0, 
                        delta=ChatCompletionChunkDelta(
                            role="assistant",
                            content=DummyLlm.__random_sentence(random.randint(1, 3))
                        ), 
                        finish_reason="")
                    ]
                )
        yield ChatCompletionChunk(
            id = "dummy", 
            model=model, 
            object="chat.completion.chunk", 
            created=0, 
            choices=[
                ChatCompletionChunkChoice(
                    index=0, 
                    delta=ChatCompletionChunkDelta(
                        role="assistant",
                        content=DummyLlm.__random_sentence(random.randint(1, 3))
                    ), 
                    finish_reason="stop")
                ]
            )

    def create_chat_completion(
        self,
        messages: list[ChatCompletionMessage],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.9, 
        max_tokens: int = -1, 
        top_p: float = 1, 
        frequency_penalty: float = 0, 
        presence_penalty: float = 0,
        n: int = 1,
        stream: bool = False
    ) -> ChatCompletion | Iterator[ChatCompletionChunk]:
        if stream:
            return self.__dummy_stream(messages, model, max_tokens)
        received = "\n".join([f"[{x['role']}]: '''{x['content']}'''" for x in messages])
        return ChatCompletion(
            id = "dummy", 
            object="chat.completion",
            created=0, 
            model=model, 
            choices=[
                ChatCompletionChoice(
                    index=0, 
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=f'Received message: {received}\n\nAnswer: ' + DummyLlm.__random_sentence()
                    ), 
                    finish_reason="stop")
                ],
            usage= CompletionUsage(
                prompt_tokens=100,
                completion_tokens=100,
                total_tokens=200
            )
        )
def get_models() -> list[Model]:
    return openai.Model.list() # type: ignore