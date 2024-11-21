import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # To allow cross-origin requests

# Store the recipe responses in a dictionary (cache the data)
recipe_data_cache = {}

# Step 1: Define the function to get recipe IDs based on ingredients
def fetch_recipe_ids(ingredient_used, ingredient_not_used, page=1, page_size=2):
    url = f"https://cosylab.iiitd.edu.in/recipe-search/recipesByIngredient?page={page}&pageSize={page_size}"
    data = {
        "ingredientUsed": ingredient_used,
        "ingredientNotUsed": ingredient_not_used
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        response_data = response.json()
        if response_data["success"] == "true":
            recipes = response_data["payload"]["data"]
            recipe_ids = [recipe["Recipe_id"] for recipe in recipes]
            return recipe_ids
        else:
            print("Failed to fetch recipes:", response_data["message"])
            return []
    else:
        print(f"Error in fetching recipe IDs: {response.status_code}")
        return []

# Step 2: Define the function to fetch full recipe details and store them in the cache
def fetch_and_cache_recipe_details(recipe_ids):
    base_url = "https://cosylab.iiitd.edu.in/recipe"
    
    # Check if the recipe data is already cached, if not, fetch and store
    for recipe_id in recipe_ids:
        if recipe_id not in recipe_data_cache:  # Fetch only if not cached
            url = f"{base_url}/{recipe_id}"
            response = requests.get(url)
            if response.status_code == 200:
                recipe_details = response.json()
                # Store the full recipe data in the cache (dictionary)
                recipe_data_cache[recipe_id] = recipe_details
            else:
                print(f"Failed to fetch details for Recipe ID {recipe_id}: {response.status_code}")

# Route to handle recipe search requests
@app.route('/search', methods=['POST'])
def search_recipes():
    ingredient_used = request.json.get("ingredientUsed", "")
    ingredient_not_used = request.json.get("ingredientNotUsed", "")
    page = request.json.get("page", 1)  # Get current page number from frontend
    
    # Fetch recipe IDs based on the ingredients
    recipe_ids = fetch_recipe_ids(ingredient_used, ingredient_not_used, page=page)
    
    if recipe_ids:
        # Fetch and store the full details of the recipes in cache
        fetch_and_cache_recipe_details(recipe_ids)
        
        # Prepare the response with Name, Ingredients, and Process using cached data
        recipes = []
        for recipe_id in recipe_ids:
            if recipe_id in recipe_data_cache:
                recipe_response = recipe_data_cache[recipe_id]
                try:
                    name = recipe_response["payload"]["Recipe_title"]
                    ingredients = recipe_response["payload"]["ingredients"]
                    instructions = recipe_response["payload"]["instructions"]
                    calories = recipe_response["payload"]["Calories"]
                    prep_time = recipe_response["payload"]["prep_time"]
                    total_time = recipe_response["payload"]["total_time"]
                    img_url = recipe_response["payload"]["img_url"]
                    url = recipe_response["payload"]["url"]
                    
                    # Extract necessary details
                    recipe = {
                        "name": name,
                        "calories": calories,
                        "prep_time": prep_time,
                        "total_time": total_time,
                        "url": url,
                        "image_url": img_url,
                        "ingredients": [
                            {
                                "ingredient": ingredient["ingredient"],
                                "state": ingredient.get("state", ""),
                                "quantity": ingredient["quantity"],
                            }
                            for ingredient in ingredients
                        ],
                        "process": [
                            step for step in instructions
                        ]  # Ensure instructions is a list, not a set
                    }
                    recipes.append(recipe)
                except KeyError as e:
                    print(f"Error: Missing key - {e}")
        
        # Return the prepared response in JSON format
        return jsonify({"recipes": recipes})

    return jsonify({"message": "No recipes found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
