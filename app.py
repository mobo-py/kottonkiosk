import json
from google import genai

# Load JSON data
with open("static/data/clothing.json", "r") as clothing_file:
    clothing = json.load(clothing_file)
with open("static/data/male_aesthetics.json", "r") as male_file:
    male_aesthetics = json.load(male_file)
with open("static/data/female_aesthetics.json", "r") as female_file:
    female_aesthetics = json.load(female_file)

client = genai.Client(api_key="AIzaSyCKfsTR7s2AWAF9QkH16eb8tNUYsRurEWI")
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

def pick_item_from_category(category_items, category):
    print(f"\nAvailable {category}s:")
    for idx, item in enumerate(category_items):
        name = item['data'].get('name', 'Unnamed Item')
        colors = item['data'].get('colors', {})
        if isinstance(colors, dict):
            color_list = list(colors.keys())
        else:
            color_list = colors
        print(f"{idx+1}. {name} (Colors: {', '.join(color_list)})")
    while True:
        try:
            choice = int(input(f"Pick a {category} by number (or 0 to skip): "))
            if choice == 0:
                return None, None
            if 1 <= choice <= len(category_items):
                item = category_items[choice-1]
                colors = item['data'].get('colors', {})
                if isinstance(colors, dict):
                    color_list = list(colors.keys())
                else:
                    color_list = colors
                while True:
                    color = input(f"Choose a color from {color_list}: ").strip()
                    if color in color_list:
                        # Check quantity for this color
                        qty_dict = item['data'].get('quantity', {})
                        if isinstance(qty_dict, dict):
                            qty = qty_dict.get(color, 0)
                        else:
                            qty = qty_dict
                        if qty > 0:
                            return item, color
                        else:
                            print("Sorry, that color is out of stock. Pick another color.")
                    else:
                        print("Invalid color. Try again.")
            else:
                print("Invalid choice. Try again.")
        except Exception:
            print("Invalid input. Try again.")

def update_quantity(item, color):
    qty_dict = item['data'].get('quantity', {})
    if isinstance(qty_dict, dict):
        if color in qty_dict and qty_dict[color] > 0:
            qty_dict[color] -= 1
            item['data']['quantity'] = qty_dict
    else:
        # fallback for old format
        if item['data']['quantity'] > 0:
            item['data']['quantity'] -= 1

def save_clothing():
    with open("static/data/clothing.json", "w") as clothing_file:
        json.dump(clothing, clothing_file, indent=4)

def main():
    print("Welcome to KottonKiosk!")
    shopper_gender = input("Enter gender (male/female): ").strip().lower()
    user_prompt = input("Describe your desired style: ").strip()
    keywords_response = takepromptreturnkeywords(shopper_gender, user_prompt)
    try:
        aesthetics_keywords = eval(keywords_response)
    except Exception as e:
        print("ERROR in eval of Gemini response:", e)
        aesthetics_keywords = []
    print("Gemini returned aesthetics:", aesthetics_keywords)
    filtered_items = filter_items_by_aesthetics(shopper_gender, aesthetics_keywords)

    categories = ["hat", "top", "bottom", "dress", "shoes"]
    while True:
        print("\nWhich categories do you want to include in your outfit?")
        selected = {}
        for cat in categories:
            ans = input(f"Include {cat}? (y/n): ").strip().lower()
            selected[cat] = ans == "y"
        outfit = {}
        for cat in categories:
            if selected[cat]:
                items = filtered_items[cat]
                if not items:
                    print(f"No items available for {cat} with the selected aesthetics.")
                    continue
                item, color = pick_item_from_category(items, cat)
                if item and color:
                    outfit[cat] = {"item": item, "color": color}
        print("\nYour outfit:")
        for cat, val in outfit.items():
            name = val["item"]['data'].get('name', 'Unnamed Item')
            print(f"{cat}: {name} (Color: {val['color']})")
        another = input("\nWould you like to make another outfit? (y/n): ").strip().lower()
        # Reduce quantity for purchased items
        for cat, val in outfit.items():
            update_quantity(val["item"], val["color"])
        save_clothing()
        if another != "y":
            print("Proceeding to checkout. Thank you for shopping!")
            break

if __name__ == "__main__":
    main()