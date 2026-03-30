from fastapi import FastAPI

app = FastAPI(title="Blueprint to CAD API")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
