import json

def load_icp():
    with open("config/icp.json", "r") as file:
        return json.load(file)