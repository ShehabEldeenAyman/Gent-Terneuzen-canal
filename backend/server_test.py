from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 1. Define what your data looks like (Like a TypeScript Interface)
class DataInput(BaseModel):
    name: str
    values: list[float]

# 2. Create a "GET" route
@app.get("/")
def read_root():
    return {"status": "Server is running"}

# 3. Create a "POST" route to process data
@app.post("/analyze")
async def analyze_data(item: DataInput):
    # Perform Python-specific logic (e.g., math or data science)
    total = sum(item.values)
    average = total / len(item.values) if item.values else 0
    
    return {
        "user": item.name,
        "result": {
            "sum": total,
            "avg": average
        }
    }