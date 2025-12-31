import ollama
from utils.text_parser import parse_recommendations

def generate_recommendations(preds,crop,lang="en"):
    """
        Generate a simple, farmer friendly recommendations using local LLM(via ollama)
    """

    prompt = f"""
You are a local agricultural field advisor.
Using the crop information below, give simple, clear, farmer-friendly guidance in English.

Crop: {crop}
Stage: {preds["crop_stage"]}
Recommended Fertilizer: {preds["fertilizer"]["fertilizer_name"]}
Fertilizer Amount: {preds["fertilizer"]["quantity_kg_per_acre"]} kg/acre
Irrigation Need: {preds["irrigation"]:.1f} mm/day
Predicted Yield: {preds["yield"]:.1f} kg/acre

Instructions:
• Use very simple words a farmer can understand.
. Mention the crop stage always
• Keep each bullet short (1 sentence).
• Do NOT use technical jargon.
• Give only 3-4 practical bullet points.
• Focus on what the farmer should do right now.
"""
    response=ollama.chat(
            model="gemma2:2b",
            messages=[{'role':'user','content':prompt}]
        )
    # parsed = parse_recommendations(response["message"]["content"])
    return response["message"]["content"]