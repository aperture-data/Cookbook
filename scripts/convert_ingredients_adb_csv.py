from pandas import read_csv
from uuid import uuid4


if __name__ == "__main__":
    df = read_csv("../ingredients.csv")
    ingredients = df[["id", "ingredient_name"]]
    ingredients = ingredients.assign(EntityClass="Ingredient")
    ingredients["UUID"] = [uuid4() for _ in range(len(ingredients))]
    ingredients = ingredients.rename(columns={"id": "dish_id"})
    ingredients = ingredients[["EntityClass", "UUID", "dish_id", "ingredient_name"]]
    ingredients["constraint_UUID"] = ingredients["UUID"]
    ingredients.to_csv("ingredients.adb.csv", index=False)
    print("Written to ingredients.adb.csv")

    dishes = read_csv("../images.adb.csv")
    dishes["UUID"] = [uuid4() for _ in range(len(dishes))]
    dishes.to_csv("dishes.adb.csv", index=False)
    print("Written to dishes.adb.csv")

    joins = dishes[["id"]].merge(ingredients[["UUID", "dish_id"]], left_on="id", right_on="dish_id")
    joins = joins.rename(columns={"id": "_Image@id", "UUID": "Ingredient@UUID"})
    joins = joins.assign(ConnectionClass="HasIngredient")
    joins = joins[['ConnectionClass', '_Image@id', 'Ingredient@UUID']]
    joins.to_csv("dish_ingredients.adb.csv", index=False)
    print("Written to dish_ingredients.adb.csv")