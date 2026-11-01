"""Run Hajj-AI V5.1 with bounded retries for temporary Gemini errors.

Copy this file next to run_experiment.py and pass the usual arguments.
Does not modify the baseline, prompts, model settings or resume fingerprint.
Only retries the individual API request that received a transient HTTP error.
"""
from __future__ import annotations

import random
import re
import sys
import time

from hajj_baseline.providers import LLMProvider, ProviderError

                                                                            
RETRY_DELAYS_SECONDS = (4, 10, 22, 45)
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}
_original_generate = LLMProvider.generate


def generate_with_retries(self, system_prompt, user_prompt, response_schema=None):
    for attempt in range(len(RETRY_DELAYS_SECONDS) + 1):
        try:
            return _original_generate(self, system_prompt, user_prompt, response_schema)
        except ProviderError as exc:
            match = re.search(r"Gemini returned HTTP (\d{3})(?:\D|$)", str(exc))
            status = int(match.group(1)) if match else None
            if status not in TRANSIENT_HTTP_CODES or attempt == len(RETRY_DELAYS_SECONDS):
                raise                                                        
            base_delay = RETRY_DELAYS_SECONDS[attempt]
            delay = base_delay + random.uniform(0, min(2.0, base_delay * 0.15))
            print(
                f"Gemini HTTP {status}: retrying this API call "
                f"({attempt + 1}/{len(RETRY_DELAYS_SECONDS)}) in {delay:.1f}s...",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(delay)


def main():
    LLMProvider.generate = generate_with_retries
    import run_experiment
    run_experiment.main()                                                          


if __name__ == '__main__':
    main()
