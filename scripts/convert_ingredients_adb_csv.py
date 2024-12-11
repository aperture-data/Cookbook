from pandas import read_csv
from uuid import uuid4


if __name__ == "__main__":
    sheet_id = "1G1HPG3Dxx5W39OD6b74wMHvWupD7N-DLUbV7tD5owx8"
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="

    ingredient_columns = ["Name", "other_names", "category", "subgroup", "macronutrient", "micronutrient"]
    ingredients = read_csv(f"{sheet_url}Ingredients").dropna(how="all", axis="columns")
    ingredients = ingredients[ingredient_columns]
    ingredients = ingredients.assign(EntityClass="Ingredient")


    ingredients = ingredients[["EntityClass"] + ingredient_columns]
    ingredients["constraint_Name"] = ingredients["Name"]
    ingredients.to_csv("ingredients.adb.csv", index=False)
    print("Written to ingredients.adb.csv")

    dishes = read_csv(f"{sheet_url}Dishes").dropna(how="all", axis="columns")
    dishes.insert(0, "url", dishes.pop("filename").apply(lambda x: f"https://raw.githubusercontent.com/aperture-data/Cookbook/refs/heads/main/images/{x}"))
    dishes["constraint_id"] = dishes["id"]
    dishes.to_csv("dishes.adb.csv", index=False)
    print("Written to dishes.adb.csv")

    di = read_csv(f"{sheet_url}Dish_Ingredients").dropna(how="all", axis="columns")
    joins = dishes[["id"]].merge(di, on="id", how="left").merge(ingredients, left_on="ingredient_name", right_on="Name")
    joins = joins.rename(columns={"id": "_Image@id", "Name": "Ingredient@Name"})
    joins = joins.assign(ConnectionClass="HasIngredient")
    joins["connection_id"] = joins.apply(lambda row: f"{row['_Image@id']}_{row['Ingredient@Name']}", axis=1)
    joins["constraint_connection_id"] = joins["connection_id"]
    joins = joins[['ConnectionClass', '_Image@id', 'Ingredient@Name', "connection_id", "constraint_connection_id"]]
    joins.to_csv("dish_ingredients.adb.csv", index=False)
    print("Written to dish_ingredients.adb.csv")