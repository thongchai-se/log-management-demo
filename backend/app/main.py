from fastapi import FastAPI


app = FastAPI(
    title="Log Management API",
    version="1.0.0"
)

@app.get("/json/version", include_in_schema=False)
async def json_version():
    return {}

@app.get("/")
def root():
    return {
        "message": "Log Management API",
        "status": "running"
   }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }