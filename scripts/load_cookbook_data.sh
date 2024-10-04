#!/bin/bash

mkdir -p data; cd data

# Get the script to generate the data.json
wget https://github.com/aperture-data/Cookbook/raw/refs/heads/main/scripts/convert_ingredients_adb_csv.py

# Run the script to generate the right CSV files
python convert_ingredients_adb_csv.py

# OpenAI CLIP model for generating embeddings.
pip install git+https://github.com/openai/CLIP.git

adb ingest from-csv dishes.adb.csv --ingest-type IMAGE  --transformer common_properties --transformer image_properties --transformer clip_pytorch_embeddings
adb ingest from-csv ingredients.adb.csv --ingest-type ENTITY
adb ingest from-csv dish_ingredients.adb.csv --ingest-type CONNECTION

cd -