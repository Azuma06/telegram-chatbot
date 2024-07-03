import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from firebase_admin import firestore


def generate_last_month_report():
    # Initialize Firestore client
    db = firestore.client()

    # Calculate the date range for the current month
    today = datetime.date.today()
    first_day_of_this_month = today.replace(day=1)
    next_month = first_day_of_this_month.replace(day=28) + datetime.timedelta(days=4)
    last_day_of_this_month = next_month - datetime.timedelta(days=next_month.day)

    # Query the database for this month's appointments
    appointments = db.collection('appointments').where(
        filter=firestore.FieldFilter('date', '>=', first_day_of_this_month.strftime('%Y-%m-%d'))
    ).where(
        filter=firestore.FieldFilter('date', '<=', last_day_of_this_month.strftime('%Y-%m-%d'))
    ).get()

    # Prepare data for the report
    data = [['Date', 'Time', 'Service', 'Employee', 'Customer', 'Price']]
    total_revenue = 0

    # Define price mapping
    price_mapping = {
        'corte': 50,
        'hidratacao': 40,
        'manicure': 30,
        'pedicure': 40,
        'tintura': 70
    }

    for appt in appointments:
        appt_data = appt.to_dict()
        service = appt_data.get('service', 'N/A')
        price = price_mapping.get(service.lower(), 0)  # Default to 0 if service not found

        data.append([
            appt_data.get('date', 'N/A'),
            appt_data.get('time', 'N/A'),
            service,
            appt_data.get('employee', 'N/A'),
            f"{appt_data.get('first_name', 'N/A')} {appt_data.get('last_name', 'N/A')}",
            f"R${price}"
        ])
        total_revenue += price

    # Create the PDF
    pdf_filename = f"monthly_report_{first_day_of_this_month.strftime('%Y_%m')}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    elements = []

    # Add title
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Monthly Report - {first_day_of_this_month.strftime('%B %Y')}", styles['Title']))

    # Add table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)

    # Add total revenue
    elements.append(Paragraph(f"Total Revenue: R${total_revenue}", styles['Heading2']))

    # Build the PDF
    doc.build(elements)
    print(f"Report generated: {pdf_filename}")
    return pdf_filename


if __name__ == "__main__":
    generate_last_month_report()