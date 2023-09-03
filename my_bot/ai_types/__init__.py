from typing import Any, AsyncGenerator, Awaitable, Coroutine, Iterator, List, Optional, Dict, Protocol, Union
from typing_extensions import TypedDict, NotRequired, Literal


class EmbeddingUsage(TypedDict):
    prompt_tokens: int
    total_tokens: int


class EmbeddingData(TypedDict):
    index: int
    object: str
    embedding: List[float]


class Embedding(TypedDict):
    object: Literal["list"]
    model: str
    data: List[EmbeddingData]
    usage: EmbeddingUsage


class CompletionLogprobs(TypedDict):
    text_offset: List[int]
    token_logprobs: List[Optional[float]]
    tokens: List[str]
    top_logprobs: List[Optional[Dict[str, float]]]


class CompletionChoice(TypedDict):
    text: str
    index: int
    logprobs: Optional[CompletionLogprobs]
    finish_reason: Optional[str]


class CompletionUsage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionChunk(TypedDict):
    id: str
    object: Literal["text_completion"]
    created: int
    model: str
    choices: List[CompletionChoice]


class Completion(TypedDict):
    id: str
    object: Literal["text_completion"]
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: CompletionUsage


class ChatCompletionMessage(TypedDict):
    role: Literal["assistant", "user", "system", "function"]
    content: str
    name: NotRequired[str]
    function_call: NotRequired[Any]


class ChatCompletionChoice(TypedDict):
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str]


class ChatCompletion(TypedDict):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: CompletionUsage

class ChatCompletionChunkDeltaEmpty(TypedDict):
    pass

class ChatCompletionChunkDelta(TypedDict):
    role: NotRequired[Literal["assistant"]]
    content: NotRequired[str]


class ChatCompletionChunkChoice(TypedDict):
    index: int
    delta: Union[ChatCompletionChunkDelta, ChatCompletionChunkDeltaEmpty]
    finish_reason: Optional[str]


class ChatCompletionChunk(TypedDict):
    id: str
    model: str
    object: Literal["chat.completion.chunk"]
    created: int
    choices: List[ChatCompletionChunkChoice]

class Model(TypedDict):
    id: str
    object: str
    created: int
    owned_by: str

class OpenLlm(Protocol):
    def create_chat_completion(
        self,
        messages: list[ChatCompletionMessage],
        model: str,
        temperature: float = 0.9, 
        max_tokens: int = -1, 
        top_p: float = 1, 
        frequency_penalty: float = 0, 
        presence_penalty: float = 0,
        n: int = 1,
        stream: bool = False
    ) -> Iterator[ChatCompletionChunk] | ChatCompletion: ...

class AsyncOpenLlm(Protocol):
    def acreate_chat_completion(
        self,
        messages: list[ChatCompletionMessage],
        model: str,
        temperature: float = 0.9, 
        max_tokens: int = -1, 
        top_p: float = 1, 
        frequency_penalty: float = 0, 
        presence_penalty: float = 0,
        n: int = 1,
        stream: bool = False
    ) -> Awaitable[ChatCompletion] | AsyncGenerator[ChatCompletionChunk, None]: ...