from typing import List, Dict, Optional
from index import call_llm_haiku_via_messages

async def summarize_reviews(reviews: List[Dict[str, Optional[str]]]) -> None:
    prompt = f"""
    You will be analyzing a set of Airbnb reviews. Your task is to create a summary of all reviews, highlight positive points, and identify negative points from these reviews. Here are the steps to follow:
1. First, carefully read and analyze all the reviews provided in the following section:
<reviews>
    {"".join([f"<review><review_by>{review['name']}</review_by><content>{review['content']}</content></review>\n" for review in reviews if review['content']])}
</reviews>
2. After analyzing all the reviews, create a concise summary that captures the overall sentiment and main points mentioned across all reviews. This summary should be a paragraph or two in length.
3. Next, identify the positive points mentioned in the reviews. These should be specific aspects that guests frequently praised or highlighted as strengths.
4. Then, identify the negative points or areas of improvement mentioned in the reviews. These should be specific aspects that guests frequently criticized or suggested could be better.
5. Think step by step and present your reasoning in <SCRATCHPAD> tag
Present your analysis in the following format, using the specified XML tags:
<RESPONSE>
    <SCRATCHPAD>your step by step reasoning here</SCRATCHPAD>
    <summary>
    [Insert your overall summary of the reviews here]
    </summary>
    <positive_points>
    - [First positive point] : [name of the guest]
    - [Second positive point] : [name of the guest]
    - [Third positive point] : [name of the guest]
    [Continue with additional positive points as needed]  : [name of the guest]
    </positive_points>
    <negative_points>
    - [First negative point] : [name of the guest]
    - [Second negative point] : [name of the guest]
    - [Third negative point] : [name of the guest]
    [Continue with additional negative points as needed] : [name of the guest]
    </negative_points>
<RESPONSE>
Remember to be objective in your analysis, basing your summary and points strictly on the content of the reviews provided. Ensure that your positive and negative points are clear, concise, and reflect the most commonly mentioned aspects in the reviews."""

    response = await call_llm_haiku_via_messages(
        system="",
        messages=[
            {
                "content": prompt,
                "role": "user",
            }
        ],
        user="local",
        temperature=0,
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        meta={"type": "review_summary"}
    )
    print(response)
    return response