from workers.celery_app import celery


@celery.task
def test_ingestion(job_id: str):
    print(f"\n🚀 Processing Job: {job_id}\n")

    return True