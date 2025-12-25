from fastapi import FastAPI
from service.ARL import AssociationRulesMiner

miner = AssociationRulesMiner(csv_path='Transactions.csv', json_cache_path='data.json')

app = FastAPI()

@app.get("/")
def get_pairs():
    return "It`s root dir.         /api/ARLs - the ARL results data"

@app.get("/api/pairs")
def get_pairs():
    return miner.get_pairs()
