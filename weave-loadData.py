from weaviate import Client
import json
import requests

# Initialize Weaviate client
client = Client(
    url="http://localhost:8080/",
)

# Specify schema for the data we'll be using
try:
    client.schema.delete_class("SimSearch")  # Delete the class if it already exists
except Exception as e:
    print(f"Warning: {e}")

class_obj = {
    "class": "SimSearch",
    "vectorizer": "text2vec-transformers"
}
client.schema.create_class(class_obj)

# Download data
url = 'http://localhost:8000/data.json'  # URL of the JSON file being served
resp = requests.get(url)
data = json.loads(resp.text)

# Send data to Weaviate, to vectorize
with client.batch as batch:
    batch.batch_size = 100  # Adjust batch size if needed
    # Batch import all data
    for i, d in enumerate(data):
        print(f"\nImporting datum: {i}")

        properties = {
            "Author": d["Author"],
            "Book": d["Book"],
            "Summary": d["Summary"],
        }
        print(f"Properties: {properties}")

        client.batch.add_data_object(properties, "SimSearch")
