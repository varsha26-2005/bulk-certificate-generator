from pathlib import Path
import csv
import io
import zipfile

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, Job, Certificate
from app.schemas import GenerationRequest
from app.certificate_generator import create_certificate


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Bulk Certificate Generator API",
    description="API for generating certificates in bulk.",
    version="1.0.0"
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Bulk Certificate Generator API is running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# =========================================================
# CREATE JOB USING JSON
# =========================================================

@app.post("/jobs")
def create_generation_job(
    request: GenerationRequest,
    db: Session = Depends(get_db)
):
    job = Job(
        status="PROCESSING",
        total=len(request.recipients),
        successful=0,
        failed=0
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    for recipient in request.recipients:

        certificate = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            status="PROCESSING"
        )

        db.add(certificate)
        db.commit()
        db.refresh(certificate)

        try:

            file_path = create_certificate(
                recipient_name=recipient.name,
                event_name=request.event_name,
                event_date=request.event_date,
                job_id=job.id,
                certificate_id=certificate.id
            )

            certificate.status = "COMPLETED"
            certificate.file_path = file_path

            job.successful += 1

        except Exception as error:

            certificate.status = "FAILED"
            certificate.error_message = str(error)

            job.failed += 1

        db.commit()

    if job.failed == 0:
        job.status = "COMPLETED"

    elif job.successful == 0:
        job.status = "FAILED"

    else:
        job.status = "PARTIAL"

    db.commit()

    return {
        "job_id": job.id,
        "status": job.status,
        "total": job.total,
        "successful": job.successful,
        "failed": job.failed
    }


# =========================================================
# CREATE JOB USING CSV
# =========================================================

@app.post("/jobs/csv")
async def create_csv_generation_job(
    event_name: str,
    event_date: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # Check file type
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file."
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported."
        )

    # Read uploaded file
    contents = await file.read()

    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV file must use UTF-8 encoding."
        )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    if not reader.fieldnames:
        raise HTTPException(
            status_code=400,
            detail="CSV file is empty."
        )

    # Normalize column names
    fieldnames = [
        field.strip().lower()
        for field in reader.fieldnames
    ]

    if "name" not in fieldnames:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain a 'name' column."
        )

    if "email" not in fieldnames:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain an 'email' column."
        )

    recipients = []

    for row in reader:

        normalized_row = {
            key.strip().lower(): value.strip()
            if value else ""
            for key, value in row.items()
            if key
        }

        name = normalized_row.get("name", "")
        email = normalized_row.get("email", "")

        if not name or not email:
            continue

        recipients.append({
            "name": name,
            "email": email
        })

    if not recipients:
        raise HTTPException(
            status_code=400,
            detail="No valid recipients found in CSV."
        )

    # Create job
    job = Job(
        status="PROCESSING",
        total=len(recipients),
        successful=0,
        failed=0
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Generate certificates
    for recipient in recipients:

        certificate = Certificate(
            job_id=job.id,
            recipient_name=recipient["name"],
            recipient_email=recipient["email"],
            status="PROCESSING"
        )

        db.add(certificate)
        db.commit()
        db.refresh(certificate)

        try:

            file_path = create_certificate(
                recipient_name=recipient["name"],
                event_name=event_name,
                event_date=event_date,
                job_id=job.id,
                certificate_id=certificate.id
            )

            certificate.status = "COMPLETED"
            certificate.file_path = file_path

            job.successful += 1

        except Exception as error:

            certificate.status = "FAILED"
            certificate.error_message = str(error)

            job.failed += 1

        db.commit()

    # Final status
    if job.failed == 0:
        job.status = "COMPLETED"

    elif job.successful == 0:
        job.status = "FAILED"

    else:
        job.status = "PARTIAL"

    db.commit()

    return {
        "job_id": job.id,
        "status": job.status,
        "total": job.total,
        "successful": job.successful,
        "failed": job.failed
    }


# =========================================================
# GET JOB STATUS
# =========================================================

@app.get("/jobs/{job_id}")
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
):

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    certificates = (
        db.query(Certificate)
        .filter(Certificate.job_id == job.id)
        .all()
    )

    return {
        "job_id": job.id,
        "status": job.status,
        "total": job.total,
        "successful": job.successful,
        "failed": job.failed,

        "certificates": [
            {
                "id": certificate.id,
                "recipient_name": certificate.recipient_name,
                "recipient_email": certificate.recipient_email,
                "status": certificate.status,
                "file_path": certificate.file_path,
                "error_message": certificate.error_message
            }

            for certificate in certificates
        ]
    }


# =========================================================
# DOWNLOAD INDIVIDUAL CERTIFICATE
# =========================================================

@app.get("/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):

    certificate = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id)
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found"
        )

    if certificate.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Certificate is not available for download"
        )

    if not certificate.file_path:
        raise HTTPException(
            status_code=404,
            detail="Certificate file path not found"
        )

    file_path = Path(certificate.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Certificate file does not exist"
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_path.name
    )


# =========================================================
# DOWNLOAD ALL CERTIFICATES AS ZIP
# =========================================================

@app.get("/jobs/{job_id}/download")
def download_all_certificates(
    job_id: int,
    db: Session = Depends(get_db)
):

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    certificates = (
        db.query(Certificate)
        .filter(
            Certificate.job_id == job_id,
            Certificate.status == "COMPLETED"
        )
        .all()
    )

    if not certificates:
        raise HTTPException(
            status_code=404,
            detail="No completed certificates found for this job"
        )

    output_dir = Path("generated")

    output_dir.mkdir(
        exist_ok=True
    )

    zip_path = (
        output_dir /
        f"job_{job_id}_certificates.zip"
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:

        for certificate in certificates:

            if not certificate.file_path:
                continue

            pdf_path = Path(
                certificate.file_path
            )

            if pdf_path.exists():

                zip_file.write(
                    pdf_path,
                    arcname=pdf_path.name
                )

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=zip_path.name
    )