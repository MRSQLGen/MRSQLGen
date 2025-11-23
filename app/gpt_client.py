import os
import time
import logging
from typing import List, Tuple
import openai
import requests

#
# Default model name
DEFAULT_MODEL = "gpt-4o-mini"

# （）
# Default temperature (controls randomness of output)
DEFAULT_TEMPERATURE = 0.0

#
# Default number of retry attempts
DEFAULT_RETRY_CNT = 3

# （）
# Default delay between retries in seconds
DEFAULT_RETRY_DELAY = 5


class GPTClient:
    """ OpenAI ，
    A wrapper around OpenAI chat completions with retry logic and internal logging."""

    def __init__(
            self,
            model_name: str = DEFAULT_MODEL,
            llm_type: str = "general-purpose",
            temperature: float = DEFAULT_TEMPERATURE,
            api_key: str | None = None,
            api_base: str | None = None,
            url: str = "http://localhost:11436/api/chat",
            stream: bool = False,
            retry_cnt: int = DEFAULT_RETRY_CNT,
            retry_delay: int = DEFAULT_RETRY_DELAY,
            log_file: str = "gpt_client.log",
            log_level: int = logging.DEBUG,
    ) -> None:
        #
        # Initialize logger
        self.logger = self._setup_logger(log_file, log_level)

        #
        # Set model name and temperature
        self.model_name = model_name
        self.llm_type = llm_type
        self.temperature = temperature

        #  API  API
        # Get API key and base URL from parameters or environment variables
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or os.getenv("OPENAI_API_BASE")

        # set url for local llm
        self.url = url
        self.stream = stream

        # Set retry parameters
        self.retry_cnt = retry_cnt
        self.retry_delay = retry_delay

        #  OpenAI
        # Initialize the OpenAI client
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
        )

    def _setup_logger(self, log_file: str, level: int) -> logging.Logger:
        """：
        Internal method: initialize the logger"""
        logger = logging.getLogger("GPTClient")
        logger.setLevel(level)
        logger.propagate = False  # / Prevent duplicate log output

        if not logger.handlers:  # handler / Avoid adding handlers multiple times
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            #
            # File handler
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(formatter)
            fh.setLevel(level)
            logger.addHandler(fh)

            #
            # Stream (console) handler
            sh = logging.StreamHandler()
            sh.setFormatter(formatter)
            sh.setLevel(level)
            logger.addHandler(sh)

        return logger
    def generate_general_llm(self, messages):
        #  OpenAI Chat API
        # Call OpenAI chat API
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
        )
        choice = response.choices[0]
        usage = response.usage
        return (
            choice.message.content,
            (
                usage.completion_tokens,
                usage.prompt_tokens,
                usage.total_tokens,
            ),
        )



    # def generate_general_llm(self, messages):
    #     for attempt in range(1, self.retry_cnt + 1):
    #         try:
    #             #  OpenAI Chat API
    #             # Call OpenAI chat API
    #             response = self.client.chat.completions.create(
    #                 model=self.model_name,
    #                 messages=messages,
    #                 temperature=self.temperature,
    #             )
    #             choice = response.choices[0]
    #             usage = response.usage
    #             return (
    #                 choice.message.content,
    #                 (
    #                     usage.completion_tokens,
    #                     usage.prompt_tokens,
    #                     usage.total_tokens,
    #                 ),
    #             )
    #         except Exception as e:
    #             #
    #             # Log error on exception
    #             self.logger.error(
    #                 "general_llm Attempt %d/%d: failed to call OpenAI API: %s",
    #                 attempt,
    #                 self.retry_cnt,
    #                 e,
    #             )
    #             if attempt == self.retry_cnt:
    #                 #
    #                 # Raise the exception if all retries have failed
    #                 raise
    #             #
    #             # Wait before next retry
    #             time.sleep(self.retry_delay)

    def generate_local_llm(self, messages):
        headers = {
            "Content-Type": "application/json"
        }
        #  localhost
        os.environ["NO_PROXY"] = "localhost"

        item = {
            "model": self.model_name,
            "messages": messages,
            "stream": self.stream,
            "temperature": self.temperature
        }

        for attempt in range(1, self.retry_cnt + 1):
            try:
                completion_tokens = 0
                prompt_tokens = 0
                total_tokens = 0
                response = requests.post(self.url, headers=headers, json=item)
                if response.status_code == 200:
                    return (
                        response.json().get("message").get("content"),
                        (
                            completion_tokens,
                            prompt_tokens,
                            total_tokens,
                        ),
                    )
                else:
                    return (
                        response.text,
                        (
                            completion_tokens,
                            prompt_tokens,
                            total_tokens,
                        ),
                    )
            except Exception as e:
                #
                # Log error on exception
                self.logger.error(
                    "local_llm Attempt %d/%d: failed to call API: %s",
                    attempt,
                    self.retry_cnt,
                    e,
                )
                if attempt == self.retry_cnt:
                    #
                    # Raise the exception if all retries have failed
                    raise
                #
                # Wait before next retry
                time.sleep(self.retry_delay)

    def generate(
            self,
            messages: List[dict],
    ) -> Tuple[str, Tuple[int, int, int]]:
        """
        Generate chat completion from input messages

         / Args:
            messages: ， OpenAI
                      A list of message dicts in the format required by OpenAI

         / Returns:
            Tuple:
                -  / The generated text content
                - token  (completion_tokens, prompt_tokens, total_tokens)   Token usage: completion, prompt, and total
        """
        if self.llm_type.lower() == "local":
            # ["deepseek-coder-v2:16b", "codellama:13b-instruct", "qwen2.5-coder:14b", "starcoder2:15b-instruct"]
            return self.generate_local_llm(messages)
        else:
            return self.generate_general_llm(messages)
