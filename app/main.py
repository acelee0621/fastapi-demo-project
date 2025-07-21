from fastapi import FastAPI, Response

app = FastAPI()


@app.get("/health")
async def health_check(response: Response):
    response.status_code = 200
    return {"status": "ok 👍 "}
