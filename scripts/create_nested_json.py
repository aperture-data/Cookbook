from pandas import read_csv
import os
import json

DISHES_CSV_PATH = "../images.adb.csv"
INGREDIENTS_CSV_PATH = "../ingredients.csv"

print(os.getcwd())
dishes = read_csv(DISHES_CSV_PATH)
ingredients = read_csv(INGREDIENTS_CSV_PATH)

json_rep = json.loads(dishes.to_json(orient="records"))

def remove_extra(selected):
    for ing in selected:
        extra = ["id",
                "name",
                "filename"]
        [ing.pop(k) for k in extra if k in ing]
        for k in ing.copy():
            if not ing[k]:
                ing.pop(k)
    return selected.copy()


if __name__ == "__main__":
    tweaked = []
    for dish in json_rep:
        dkv = dish.copy()
        dkv["dish_id"] = dkv.pop("id")
        dkv["recipe_url"] = dkv.pop("Recipe URL")
        try:
            selected = ingredients[ingredients["id"] == dkv["dish_id"]].to_json(orient="records")
            selected = json.loads(selected)
            selected = remove_extra(selected)
            dkv["ingredients"] = selected
            tweaked.append(dkv)
        except Exception as e:
            print(e)

    json.dump(tweaked, open("dishes.json", "w"), indent=4)
    print("Written to dishes.json")