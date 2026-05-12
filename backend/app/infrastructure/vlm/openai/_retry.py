"""OpenAI API 呼び出し用のリトライヘルパー。

OpenAI SDK 標準のリトライ（max_retries）に加えて、上位レイヤでも
指数バックオフリトライをかけることで断続的な障害を多段的に救済する。
"""
from __future__ import annotations

import logging
import random
import time
from typing import Callable, TypeVar

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

T = TypeVar("T")

SDK_MAX_RETRIES = 5
SDK_TIMEOUT = 120.0

WRAPPER_MAX_RETRIES = 3
WRAPPER_INITIAL_DELAY = 2.0
WRAPPER_MAX_DELAY = 30.0
WRAPPER_BACKOFF_FACTOR = 2.0

_log = logging.getLogger(__name__)

_RETRY_EXCEPTIONS = (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)


def call_with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int = WRAPPER_MAX_RETRIES,
    initial_delay: float = WRAPPER_INITIAL_DELAY,
    max_delay: float = WRAPPER_MAX_DELAY,
    backoff: float = WRAPPER_BACKOFF_FACTOR,
) -> T:
    delay = initial_delay
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except _RETRY_EXCEPTIONS as e:
            last_exc = e
            if attempt >= max_retries:
                break
            jitter = random.uniform(0.0, 0.3 * delay)
            wait = min(delay + jitter, max_delay)
            _log.warning(
                f"[openai-retry] {type(e).__name__}: {str(e)[:80]} "
                f"-> attempt {attempt + 1}/{max_retries + 1} after {wait:.1f}s"
            )
            time.sleep(wait)
            delay *= backoff
    assert last_exc is not None
    raise last_exc
