from app.database import SessionLocal
from app.services.crawler import create_job, run_job


def main() -> None:
    db = SessionLocal()
    try:
        job = create_job(db, "full")
        run_job(db, job.id)
        print(f"finished job #{job.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

