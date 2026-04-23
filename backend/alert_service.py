"""
alert_service.py
Sends email alerts to the parent linked to a student.
Looks up parent email from DB when student_id is provided.
"""

import smtplib
from email.message import EmailMessage
import os
from database import students_collection, parents_collection


class AlertService:

    def __init__(self):
        self.sender_email    = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        # fallback static receiver (used only if student_id not provided)
        self.default_receiver = os.getenv("RECEIVER_EMAIL")

    def _get_parent_email(self, student_id: str) -> str | None:
        """Look up the parent's email for a given student_id."""
        student = students_collection.find_one({"student_id": str(student_id)})
        if not student:
            return None

        # Try direct parent_email field first
        if student.get("parent_email"):
            return student["parent_email"]

        # Try resolving via parent_id → parents collection
        parent_id = student.get("parent_id")
        if parent_id:
            from bson import ObjectId
            try:
                parent = parents_collection.find_one({"_id": ObjectId(parent_id)})
                if parent:
                    return parent.get("email")
            except Exception:
                pass

        return None

    def send_email_alert(
        self,
        image_path: str,
        subject: str = "⚠️ AttenTrack Alert",
        student_id: str | None = None,
    ):
        if not self.sender_email or not self.sender_password:
            print("❌ Missing email credentials in .env")
            return

        # Resolve recipient
        receiver = None
        if student_id:
            receiver = self._get_parent_email(student_id)
            if receiver:
                print(f"📧 Sending alert to parent: {receiver}")
            else:
                print(f"⚠️  No parent email found for student {student_id}, using default")

        if not receiver:
            receiver = self.default_receiver

        if not receiver:
            print("❌ No recipient email available — alert not sent")
            return

        msg            = EmailMessage()
        msg["Subject"] = subject
        msg["From"]    = self.sender_email
        msg["To"]      = receiver
        msg.set_content(
            "⚠️ AttenTrack Alert\n\n"
            f"Student {student_id or 'unknown'} is not paying attention.\n"
            "Screenshot attached.\n\n"
            "— AttenTrack System"
        )

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="image",
                    subtype="jpeg",
                    filename=os.path.basename(image_path),
                )
            print("📎 Screenshot attached")
        else:
            print("⚠️  Screenshot not found:", image_path)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.send_message(msg)
            print("✅ Alert email sent to", receiver)
        except Exception as e:
            print("❌ Email failed:", e)
