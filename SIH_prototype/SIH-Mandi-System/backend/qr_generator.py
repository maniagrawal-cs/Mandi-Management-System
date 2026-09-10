"""
qr_generator.py
-----------------
Small helper file that generates a QR code image for a given piece
of text (in our case, a Gate Pass ID).

We use the third-party "qrcode" library instead of writing our own
QR code logic, exactly as recommended for this prototype.

The QR code is returned as a base64-encoded PNG string so that the
frontend can display it directly inside an <img> tag, like this:

    <img src="data:image/png;base64,....." />

This avoids having to save image files to disk and manage cleanup.
"""

import qrcode
import io
import base64


def generate_qr_base64(data: str) -> str:
    """
    Generates a QR code for the given text/data and returns it as a
    base64 string (ready to be used inside an <img src="..."> tag).
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image into memory (instead of a file on disk).
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Convert the raw image bytes into a base64 text string.
    base64_string = base64.b64encode(buffer.read()).decode("utf-8")

    return f"data:image/png;base64,{base64_string}"
