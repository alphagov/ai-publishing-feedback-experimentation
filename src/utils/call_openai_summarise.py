from openai import OpenAI
import tiktoken


class Summariser:
    def __init__(
        self,
        open_api_key,
        temperature=0.0,
        max_tokens=1000,
        seed=None,
        model="gpt-3.5-turbo-0125",
    ):
        self.client = OpenAI(api_key=open_api_key)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.model = model
        self.completion_tokens = []

    def create_openai_summary_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ):
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            completion = self.client.chat.completions.create(
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                model=self.model,
                seed=self.seed,
                stream=True,
            )
            for chunk in completion:
                content = chunk.choices[0].delta.content
                self.completion_tokens.append(
                    self.get_num_tokens_from_string(content, self.model)
                )
                if content:
                    yield content

        except Exception as e:
            status = f"error: OpenAI request failed: {e}"
            print(status)
            return {}, 0, status

    def create_openai_summary(
        self,
        system_prompt: str,
        user_prompt: str,
    ):
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            completion = self.client.chat.completions.create(
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                model=self.model,
                seed=self.seed,
                stream=False,
            )

            content = completion.choices[0].message.content
            self.completion_tokens.append(completion.usage.completion_tokens)
            return content, "success"

        except Exception as e:
            status = f"error: OpenAI request failed: {e}"
            print(status)
            return {}, 0, status

    def get_num_tokens_from_string(self, string: str, model: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(model)
        num_tokens = len(encoding.encode(string))
        return num_tokens
