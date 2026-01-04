
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf(data, ai):
    filename = "crop_report.pdf"
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    content = [
        Paragraph(f"Crop: {data.crop}", styles['Normal']),
        Paragraph(f"Health: {ai['health']}", styles['Normal']),
        Paragraph(f"Recommendation: {ai['recommendation']}", styles['Normal']),
    ]
    doc.build(content)
    return {
        "crop": data.crop,
        "health": ai["health"],
        "recommendation": ai["recommendation"],
        "pdf": filename
    }
