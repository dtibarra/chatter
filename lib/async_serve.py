import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:slack_app", port=3000, host="127.0.0.1")
