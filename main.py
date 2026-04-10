from backend.main import app
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


def main() -> None:
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
