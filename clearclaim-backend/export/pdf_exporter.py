from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

def generate_pdf(parsed, validation) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    title = Paragraph(f"ClearClaim EDI Report: {parsed.file_name}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    meta_data = [
        ["Property", "Value"],
        ["File Name", parsed.file_name],
        ["Transaction Type", parsed.transaction_type],
        ["Is Valid", str(validation.is_valid)],
        ["Error Count", str(validation.error_count)]
    ]
    t = Table(meta_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), '#d5a6a5'),
        ('GRID', (0,0), (-1,-1), 1, '#000000')
    ]))
    elements.append(t)
    elements.append(Spacer(1, 24))
    
    if validation.errors:
        err_data = [["Error Code", "Location", "Value", "Message"]]
        normal_style = styles['Normal']
        for e in validation.errors[:20]:
            err_data.append([
                e.error_code, 
                f"{e.segment_id}:{e.element_position}", 
                str(e.raw_value)[:15], 
                Paragraph(e.plain_english, normal_style)
            ])
        t2 = Table(err_data, colWidths=[80, 60, 80, 250])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), '#a5a6d5'),
            ('GRID', (0,0), (-1,-1), 1, '#000000'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(t2)
        
    doc.build(elements)
    return buffer.getvalue()