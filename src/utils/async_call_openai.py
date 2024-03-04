import asyncio

from openai import AsyncOpenAI


async def create_openai_labelled_data(
    labelled_examples: str,
    new_example: str,
    open_api_key: str,
) -> dict:
    client = AsyncOpenAI(api_key=open_api_key)

    system_prompt = """
        You are an expert tasked with categorising user feedback for the UK government, submitted through the website www.gov.uk. Your input is a JSON containing two key pieces of information: a unique identifier (id) and the user feedback (feedback).

        Your objective is to analyze the feedback and assign an appropriate label or labels that accurately categorise the feedback. These labels should reflect the concrete issues encountered or digital services raised in the feedback rather than subjective opinions or emotions.

        Every piece of feedback must receive at least one label.

        In instances where the feedback is irrelevant or does not pertain to government services (e.g., promotional content, unrelated comments), it should be categorised as "Spam".

        In instances where the feedback is unclear or ambiguous, it should be categorised as "Unknown".

        Additionally, you must assess the urgency of the feedback on a scale from 1 (low urgency) to 3 (high urgency).

        The urgency should align with whether there's a need for prompt action to fix any technical issue, or issue relating to content, on the gov.uk website or across government digital services.

        The urgency should not be a reflection of users' subjective experiences or personal circumstances, unless they are based on a technical issue or content error that needs to be addressed urgently.

        It is crucial to process this information thoughtfully, considering the potential impact of the feedback on public services and the well-being of citizens. For example, feedback reporting a broken link on a page providing vital health information would be considered more urgent than feedback suggesting a minor cosmetic change to the website’s homepage.

        Your output must be in valid JSON format, including only the id, the assigned labels, and the urgency for each piece of feedback. This structured approach ensures clarity and consistency in how feedback is processed and prioritised.

        Remember, your analysis and categorisation play a vital role in improving government digital services and ensuring that they meet the needs of the public efficiently and effectively.
        """

    user_prompt = f"""
        Before you label the following record, let's reflect on the examples provided and apply similar reasoning to ensure consistency and accuracy in our categorisation. Consider the nature of the feedback, its relevance to government services, and the immediacy with which the issue it raises should be addressed. This thoughtful approach will guide you in determining the most appropriate labels and the urgency.

        Here are the examples for reference:
        {labelled_examples}

        Based on these examples, let's proceed to categorise the new piece of feedback. Remember, we are focusing on identifying the most fitting labels and assessing the urgency accurately, all while ensuring our output is in valid JSON format. Here's the feedback you need to label:
        {new_example}

        Your output should include only the keys "id", "labels", and "urgency", and their respective values. Reflect on the content of the feedback, its implications for government services, and the potential impact on users to make your assessment. Always return your analysis in valid JSON format.
    """

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        completion = await client.chat.completions.create(
            messages=messages,  # type: ignore
            max_tokens=250,
            temperature=0.75,
            model="gpt-3.5-turbo-0125",
            response_format={"type": "json_object"},
        )
        open_labelled_records = completion.choices[0].message.content
        prompt_tokens = completion.usage.prompt_tokens
        completion_tokens = completion.usage.completion_tokens
        return {
            "open_labelled_records": open_labelled_records,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }  # type: ignore
    except Exception as e:
        print(f"OpenAI request failed: {e}")


async def get_response(
    i: str, labelled_examples: str, new_example: str, open_api_key: str
) -> dict:
    response = await create_openai_labelled_data(
        labelled_examples=labelled_examples,
        new_example=new_example,
        open_api_key=open_api_key,
    )
    return response


async def gather_responses(
    labelled_subs_json: str, new_subs_json: str, open_api_key: str
) -> list:
    responses = await asyncio.gather(
        *[
            get_response(
                i,  # type: ignore
                labelled_examples=labelled_subs_json,
                new_example=i,
                open_api_key=open_api_key,
            )
            for i in new_subs_json.split("},")  # type: ignore
        ]
    )
    return responses
