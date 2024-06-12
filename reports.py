from fpdf import FPDF
from datetime import datetime

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=9)

# Add title to the header
pdf.cell(0, 10, 'Relatório', ln=True, align='C')

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
pdf.output(f"inventario_estoque_{timestamp}.pdf")
