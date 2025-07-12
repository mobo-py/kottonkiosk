import json
from google import genai

# Load JSON data
with open("static/data/clothing.json", "r") as clothing_file:
    clothing = json.load(clothing_file)
with open("static/data/male_aesthetics.json", "r") as male_file:
    male_aesthetics = json.load(male_file)
with open("static/data/female_aesthetics.json", "r") as female_file:
    female_aesthetics = json.load(female_file)

# Create a Gemini client using an API key (ideally from an environment variable)
client = genai.Client(api_key="AIzaSyCKfsTR7s2AWAF9QkH16eb8tNUYsRurEWI")

# Shared aesthetics
shared_aesthetics = list(set(male_aesthetics + female_aesthetics))

def generate_prompt(shopper_gender, user_prompt):
    if shopper_gender.lower() == "male":
        aesthetics_list = male_aesthetics
    elif shopper_gender.lower() == "female":
        aesthetics_list = female_aesthetics
    else:
        aesthetics_list = shared_aesthetics

    conversionprompt = (
        f"You are a fashion expert. Your task is to convert a prompt into a list of aesthetics "
        f"from the following list. Your answer must be in Python syntax, and it should be the list only, "
        f"even if it's only one item long. Do not add any other text.\n\n"
        f"Aesthetics: {aesthetics_list}\n\n"
        f"For example, if the prompt is 'Generate me an outfit that doesn't have a lot going on', "
        f"your answer should be ['Minimalist']. If the prompt is 'Generate me an outfit to go to a rock concert', "
        f"your answer should be ['Punk', 'Grunge'].\n\nPrompt: {user_prompt}\n\n"
        f"This will be used to narrow down the clothing items to match the shopper's style from the following dataset:\n\n"
        f"{clothing}\n\n"
        f"Only recommend aesthetics that match the shopper's gender ('{shopper_gender}') or are unisex. "
        f"Additionally, ensure that the recommended aesthetics result in at least one piece of clothing "
        f"for each category: top, bottom, shoes, and optionally dress. "
        f"Include similar aesthetics if necessary to fulfill this requirement. "
        f"Return the list of aesthetics that match the prompt and then return their corresponding clothing items."
    )
    return conversionprompt

def takepromptreturnkeywords(shopper_gender, user_prompt):
    prompt = generate_prompt(shopper_gender, user_prompt)
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    answer = response.text
    return answer

def filter_items_by_aesthetics(shopper_gender, aesthetics_keywords):
    catalog_options = {"hat": [], "top": [], "bottom": [], "dress": [], "shoes": []}
    for item_id, item in clothing.items():
        item_gender = item.get("gender", "").lower()
        if item_gender == shopper_gender.lower() or item_gender == "unisex":
            cat = item.get("category", "").lower()
            if cat in ["footwear", "shoes"]:
                cat_key = "shoes"
            elif cat in ["hat", "cap", "fedora"]:
                cat_key = "hat"
            elif cat in ["t-shirt", "shirt", "tshirt"]:
                cat_key = "top"
            elif cat in ["pants", "trousers", "bottom"]:
                cat_key = "bottom"
            elif cat == "dress":
                cat_key = "dress"
            else:
                cat_key = None
            if cat_key:
                aesthetics_item = item.get("Aesthetic", [])
                if any(aesthetic in aesthetics_keywords for aesthetic in aesthetics_item):
                    catalog_options[cat_key].append({"id": item_id, "data": item})
    return catalog_options

# Example usage
if __name__ == "__main__":
    shopper_gender = "male"
    user_prompt = "I want a minimalist streetwear look"
    keywords_response = takepromptreturnkeywords(shopper_gender, user_prompt)
    try:
        aesthetics_keywords = eval(keywords_response)
    except Exception as e:
        print("ERROR in eval of Gemini response:", e)
        aesthetics_keywords = []
    print("Gemini returned aesthetics:", aesthetics_keywords)
    filtered_items = filter_items_by_aesthetics(shopper_gender, aesthetics_keywords)
    print("Filtered items by category:")

    # Store each category as a separate list
    hat_names = [item['data'].get('name', 'Unnamed Item') for item in filtered_items['hat']]
    top_names = [item['data'].get('name', 'Unnamed Item') for item in filtered_items['top']]
    bottom_names = [item['data'].get('name', 'Unnamed Item') for item in filtered_items['bottom']]
    dress_names = [item['data'].get('name', 'Unnamed Item') for item in filtered_items['dress']]
    shoes_names = [item['data'].get('name', 'Unnamed Item') for item in filtered_items['shoes']]

    print(f"hat: {hat_names}")
    print(f"top: {top_names}")
    print(f"bottom: {bottom_names}")
    print(f"dress: {dress_names}")
    print(f"shoes: {shoes_names}")