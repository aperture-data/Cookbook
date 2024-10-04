#!/bin/bash

mkdir -p data; cd data

# Get the script to generate the data.json
wget https://github.com/aperture-data/Cookbook/raw/refs/heads/main/scripts/convert_ingredients_adb_csv.py

# Run the script to generate the right CSV files
python convert_ingredients_adb_csv.py

# OpenAI CLIP model for generating embeddings.
pip install git+https://github.com/openai/CLIP.git

#facenet-pytorch for running ingest pipeline with transformers.
pip install facenet-pytorch --no-deps

cd -