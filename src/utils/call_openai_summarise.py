from openai import OpenAI


def create_openai_summary(
    system_prompt: str,
    user_prompt: str,
    context: str,
    open_api_key: str,
    model="gpt-3.5-turbo-0125",
    seed=None,
) -> dict:
    client = OpenAI(api_key=open_api_key)

    user_prompt = user_prompt.format(context)

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        completion = client.chat.completions.create(
            messages=messages,  # type: ignore
            max_tokens=1000,
            temperature=0.2,
            model=model,
            seed=seed,
        )
        open_summary = completion.choices[0].message.content
        prompt_tokens = completion.usage.prompt_tokens
        completion_tokens = completion.usage.completion_tokens
        return {
            "open_summary": open_summary,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }, "success"  # type: ignore
    except Exception as e:
        print(f"OpenAI request failed: {e}")
        return {}, f"error: {e}"
