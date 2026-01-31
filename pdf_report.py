from fpdf import FPDF
import datetime

class ARVReport(FPDF):
    def __init__(self, subject_address, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject_address = subject_address
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Company/Title Area - Navy Blue Background
        self.set_fill_color(10, 25, 60) # Navy Blue
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_y(10)
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 24)
        self.cell(0, 10, 'Real Estate ARV Analysis', align='C', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('helvetica', '', 12)
        self.cell(0, 8, 'Professional Valuation Report', align='C', new_x="LMARGIN", new_y="NEXT")
        
        # Subject info overlay
        self.set_y(30)
        self.set_font('helvetica', 'B', 10)
        self.cell(0, 5, f'Subject: {self.subject_address}', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(15) # Spacing after header box

    def footer(self):
        self.set_y(-20)
        self.set_text_color(128, 128, 128)
        self.set_font('helvetica', 'I', 8)
        self.multi_cell(0, 4, "Disclaimer: This report is an AI-generated estimate based on available public data. It does not constitute a formal appraisal or legal advice. Verify all data independently.", align='C')
        self.cell(0, 6, f'Page {self.page_no()}/{{nb}}', align='R')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 14)
        self.set_text_color(10, 25, 60) # Navy Blue
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", border='B')
        self.ln(5)

    def sanitize_text(self, text):
        """
        Replaces common incompatible characters with Latin-1 equivalents.
        """
        replacements = {
            '\u2013': '-',   # En-dash
            '\u2014': '--',  # Em-dash
            '\u2018': "'",   # Left single quote
            '\u2019': "'",   # Right single quote
            '\u201c': '"',   # Left double quote
            '\u201d': '"',   # Right double quote
            '\u2026': '...', # Ellipsis
            '\u00a0': ' ',   # Non-breaking space
            '**': '',        # Bold marker removal
        }
        for char, repl in replacements.items():
            text = text.replace(char, repl)
            
        return text.encode('latin-1', 'replace').decode('latin-1')

    def chapter_body(self, body):
        self.set_font('helvetica', '', 11)
        self.set_text_color(20, 20, 20)
        
        # Basic markdown parsing
        lines = body.split('\n')
        for line in lines:
            line = self.sanitize_text(line)
            
            if line.startswith('#'):
                # Header
                self.set_font('helvetica', 'B', 12)
                self.set_text_color(10, 25, 60)
                cleaned = line.lstrip('#').strip()
                self.cell(0, 8, cleaned, new_x="LMARGIN", new_y="NEXT")
                self.set_font('helvetica', '', 11)
                self.set_text_color(20, 20, 20)
            elif line.startswith('- ') or line.startswith('* '):
                # Bullet
                self.set_x(15)
                self.multi_cell(0, 6, f"- {line[2:]}")
            else:
                # Normal paragraph
                if line.strip():
                    # Safety check for horizontal space
                    if self.get_x() > (self.w - self.r_margin - 5):
                         self.set_x(self.l_margin)
                    self.multi_cell(0, 6, line)
                    self.ln(2)

    def table_header(self, headers, col_widths):
        self.set_font('helvetica', 'B', 10)
        self.set_fill_color(230, 230, 230) # Light grey
        self.set_text_color(0, 0, 0)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 10, h, border=1, align='C', fill=True)
        self.ln()

def generate_pdf(arv_text, comps_data, subject_address):
    """
    Generates a professional PDF report.
    Returns the PDF content as bytes.
    """
    pdf = ARVReport(subject_address)
    pdf.add_page()
    
    # 1. ARV Analysis Section
    pdf.chapter_title("AI Assessment & Valuation")
    pdf.chapter_body(arv_text)
    
    # 2. Comps List Section
    pdf.add_page()
    pdf.chapter_title("Verified Comparable Properties")
    
    # Table Config
    col_widths = [70, 25, 25, 20, 20, 20] # Address, Price, Date, SqFt, Bed/Bath, Dist
    headers = ["Address", "Sold Price", "Date", "SqFt", "B/B", "Mi"]
    alignments = ["L", "R", "C", "R", "C", "R"]
    
    pdf.table_header(headers, col_widths)
    
    # Table Rows
    pdf.set_font('helvetica', '', 9)
    fill = False
    
    for comp in comps_data:
        # Toggle background color
        if fill:
            pdf.set_fill_color(245, 245, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        # Format data
        addr = comp.get('address', 'N/A')
        if len(addr) > 35: addr = addr[:32] + "..."
        
        try:
            price_val = float(comp.get('price', 0))
            price = f"${price_val:,.0f}"
        except:
            price = str(comp.get('price', '-'))
            
        date = str(comp.get('date', '-'))
        sqft = str(comp.get('sqft', '-'))
        bed_bath = f"{comp.get('beds')}/{comp.get('baths')}"
        dist = f"{comp.get('distance')}m"
        
        row_data = [addr, price, date, sqft, bed_bath, dist]
        
        # Check page break
        if pdf.get_y() > 250:
            pdf.add_page()
            pdf.table_header(headers, col_widths)
            pdf.set_font('helvetica', '', 9)

        # Render Row
        line_height = 8
        for i, data in enumerate(row_data):
            # Sanitize data
            clean_data = pdf.sanitize_text(str(data))
            pdf.cell(col_widths[i], line_height, clean_data, border=1, align=alignments[i], fill=True)
        
        pdf.ln()
        fill = not fill # Toggle stripe

    return bytes(pdf.output())
