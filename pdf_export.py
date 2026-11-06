from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from xml.sax.saxutils import escape
from datetime import datetime


# Generate PDF
def generate_chat_pdf(messages, conversation_title):

    filename = "echoverse_chat.pdf"

    document = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        textColor=colors.purple,
        alignment=TA_CENTER
    )

    story = []

    story.append(
        Paragraph("EchoVerse AI", title_style)
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"Conversation: {escape(str(conversation_title))}",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            f"Exported: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 20))

    for message in messages:

        role = message["role"].capitalize()

        content = escape(message["content"]).replace("\n", "<br/>")

        story.append(
            Paragraph(f"<b>{role}</b>", styles["Heading3"])
        )

        story.append(
            Paragraph(content, styles["BodyText"])
        )

        story.append(Spacer(1, 12))

    document.build(story)

    return filename