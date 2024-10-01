from pandas import read_csv, Series
import json
import math

if __name__ == "__main__":
    sheet_id = "1G1HPG3Dxx5W39OD6b74wMHvWupD7N-DLUbV7tD5owx8"
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="

    sheet_names = ["Dishes", "Dish_Ingredients","Ingredients"]
    dishes, dish_ingredients, ingredients = [read_csv(f"{sheet_url}{sheet_name}").dropna(how="all", axis="columns") for sheet_name in sheet_names]

    combined = dishes.merge(
        dish_ingredients,
        on="id",
        how="left").merge(
            ingredients,
            left_on="ingredient_name",
            right_on="Name").rename({
                "Recipe URL": "recipe_url",
            }, axis="columns")
    combined["dish_id"] = combined.pop("id")
    combined["url"] = combined.pop("filename").apply(lambda x: f"https://raw.githubusercontent.com/aperture-data/Cookbook/refs/heads/main/images/{x}")


    def dish_ingredients_aggregator(g):
        return Series({
            "ingredients": g[["Name", "other_names", "category",
                            "subgroup", "macronutrient", "micronutrient"]].to_dict(orient="records", ),
        })

    combined = combined.groupby(["dish_id",
        "url",
        "type",
        "location",
        "cuisine",
        "recipe_url",
        "contributor",
        "caption",
        "name"]).apply(dish_ingredients_aggregator).reset_index()

    dishes = combined.to_dict(orient="records")

    for dish in dishes:
        for ing in dish["ingredients"]:
            for k in ing.copy():
                if not isinstance(ing[k], str) and math.isnan(ing[k]):
                    ing.pop(k)

    with open("dishes.json", "w") as f:
        f.write(json.dumps(dishes, indent=2))
