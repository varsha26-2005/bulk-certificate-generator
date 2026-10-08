from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# Folder where certificates are stored
OUTPUT_DIR = Path("generated")

OUTPUT_DIR.mkdir(exist_ok=True)


def create_certificate(
    recipient_name: str,
    event_name: str,
    event_date: str,
    job_id: int,
    certificate_id: int
):
    """
    Generate one certificate PDF.

    Returns:
        str: Relative path of generated PDF
    """

    safe_name = (
        recipient_name
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    filename = (
        f"{job_id}_{certificate_id}_{safe_name}.pdf"
    )

    output_path = OUTPUT_DIR / filename

    c = canvas.Canvas(
        str(output_path),
        pagesize=A4
    )

    width, height = A4

    # Border
    c.rect(
        50,
        50,
        width - 100,
        height - 100
    )

    # Title
    c.setFont(
        "Helvetica-Bold",
        28
    )

    c.drawCentredString(
        width / 2,
        height - 150,
        "CERTIFICATE OF PARTICIPATION"
    )

    # Subtitle
    c.setFont(
        "Helvetica",
        16
    )

    c.drawCentredString(
        width / 2,
        height - 220,
        "This certificate is proudly presented to"
    )

    # Recipient
    c.setFont(
        "Helvetica-Bold",
        25
    )

    c.drawCentredString(
        width / 2,
        height - 300,
        recipient_name
    )

    # Event text
    c.setFont(
        "Helvetica",
        16
    )

    c.drawCentredString(
        width / 2,
        height - 380,
        "for participating in"
    )

    # Event name
    c.setFont(
        "Helvetica-Bold",
        22
    )

    c.drawCentredString(
        width / 2,
        height - 430,
        event_name
    )

    # Date
    c.setFont(
        "Helvetica",
        14
    )

    c.drawCentredString(
        width / 2,
        height - 500,
        f"Date: {event_date}"
    )

    # Certificate ID
    c.setFont(
        "Helvetica",
        10
    )

    c.drawCentredString(
        width / 2,
        80,
        f"Certificate ID: {certificate_id}"
    )

    c.save()

    return str(output_path)