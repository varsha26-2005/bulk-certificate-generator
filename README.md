\# Bulk Certificate Generator



A FastAPI-based application that generates certificates in bulk from recipient data.



\## Features



\- Generate certificates for multiple recipients

\- Generate certificates using JSON input

\- Generate certificates using CSV upload

\- Store job and certificate information in SQLite

\- Track certificate generation status

\- Download individual certificates

\- Download all certificates as a ZIP file

\- REST API with Swagger documentation



\## Technologies Used



\- Python

\- FastAPI

\- SQLAlchemy

\- SQLite

\- ReportLab

\- Uvicorn



\## API Endpoints



\### Health



GET `/health`



Checks whether the API is running.



\### Generate Certificates



POST `/jobs`



Generates certificates using JSON recipient data.



\### Generate Certificates from CSV



POST `/jobs/csv`



Uploads a CSV file and generates certificates for all recipients.



\### Check Job Status



GET `/jobs/{job\_id}`



Returns the status and details of certificates belonging to a job.



\### Download Certificate



GET `/certificates/{certificate\_id}/download`



Downloads an individual certificate PDF.



\### Download All Certificates



GET `/jobs/{job\_id}/download`



Downloads all completed certificates for a job as a ZIP file.



\## Running the Project



Activate the virtual environment:



```powershell

.\\venv\\Scripts\\Activate.ps1

