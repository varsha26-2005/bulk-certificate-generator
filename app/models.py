from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    status = Column(String, default="PENDING")

    total = Column(Integer, default=0)

    successful = Column(Integer, default=0)

    failed = Column(Integer, default=0)

    certificates = relationship(
        "Certificate",
        back_populates="job",
        cascade="all, delete-orphan"
    )


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=False
    )

    recipient_name = Column(String, nullable=False)

    recipient_email = Column(String, nullable=False)

    status = Column(String, default="PENDING")

    file_path = Column(String, nullable=True)

    error_message = Column(String, nullable=True)

    job = relationship(
        "Job",
        back_populates="certificates"
    )