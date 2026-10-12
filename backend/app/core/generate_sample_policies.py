import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from backend.app.core.config import settings

def create_sample_policies():
    policies_dir = settings.POLICIES_DIR
    policies_dir.mkdir(parents=True, exist_ok=True)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=12
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8
    )
    h2_style = ParagraphStyle(
        'SubsectionH2',
        parent=styles['Heading3'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )

    # 1. HDFC ERGO Optima Secure 2024
    pdf_path_1 = policies_dir / "HDFC_Optima_Secure_2024.pdf"
    if not pdf_path_1.exists():
        doc1 = SimpleDocTemplate(str(pdf_path_1), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story1 = []
        
        # Page 1: Title & Scope
        story1.append(Paragraph("HDFC ERGO General Insurance Company", title_style))
        story1.append(Paragraph("<b>Policy Wording: Optima Secure Plan (Version 2024.1)</b>", h1_style))
        story1.append(Paragraph("This Policy is an evidence of the contract between the Proposer and HDFC ERGO General Insurance Company Limited. The Policy provides coverage for Medically Necessary Inpatient Hospitalization and Day Care procedures.", body_style))
        story1.append(Spacer(1, 10))
        
        story1.append(Paragraph("<b>SECTION 1: DEFINITIONS</b>", h1_style))
        story1.append(Paragraph("1.1 <b>Day Care Treatment:</b> Medical treatments or surgical procedures undertaken under General or Local Anesthesia in a Hospital in less than 24 hours because of technological advancement.", body_style))
        story1.append(Paragraph("1.2 <b>Pre-Existing Disease (PED):</b> Any condition, ailment, injury or disease that is diagnosed or for which medical advice or treatment was recommended or received within 36 months prior to the effective date of the Policy.", body_style))
        story1.append(Paragraph("1.3 <b>Single Private Room:</b> A basic single occupancy room in a Hospital with attached washroom facility.", body_style))
        story1.append(Spacer(1, 10))
        
        story1.append(Paragraph("<b>SECTION 2: SCOPE OF COVER (BENEFITS)</b>", h1_style))
        story1.append(Paragraph("2.1 <b>Inpatient Hospitalization:</b> We will cover Medically Necessary Hospitalization expenses incurred for treatment of Illness or Injury requiring a minimum of 24 consecutive hours of hospital admission.", body_style))
        story1.append(Paragraph("2.2 <b>Pre-Hospitalization Expenses:</b> Medical expenses incurred 60 days immediately before the date of hospitalization.", body_style))
        story1.append(Paragraph("2.3 <b>Post-Hospitalization Expenses:</b> Medical expenses incurred 180 days immediately after discharge from hospital.", body_style))
        story1.append(Paragraph("2.4 <b>Day Care Procedures:</b> All day care treatments requiring less than 24 hours hospitalization are covered up to Sum Insured.", body_style))
        story1.append(PageBreak())
        
        # Page 2: Sub-limits & Exclusions
        story1.append(Paragraph("<b>SECTION 3: SUB-LIMITS & ROOM RENT ELIGIBILITY</b>", h1_style))
        story1.append(Paragraph("3.1 <b>Room Rent Category:</b> Up to <b>Single Private Room</b>. There is <b>No Room Rent Capping</b> by percentage. No proportional deduction will apply to associated medical expenses if a Single Private Room is selected.", body_style))
        story1.append(Paragraph("3.2 <b>ICU Charges:</b> Covered without any sub-limit or percentage capping up to Sum Insured.", body_style))
        story1.append(Paragraph("3.3 <b>Modern Treatments & Robotic Surgery:</b> Covered up to the full Sum Insured without sub-limits.", body_style))
        story1.append(Spacer(1, 10))
        
        story1.append(Paragraph("<b>SECTION 4: EXCLUSIONS & WAITING PERIODS</b>", h1_style))
        story1.append(Paragraph("4.1 <b>Initial 30-Day Waiting Period (Code - Excl03):</b> A waiting period of 30 days from policy inception applies to all illnesses, except accidental injuries.", body_style))
        story1.append(Paragraph("4.2 <b>Pre-Existing Disease Waiting Period (Code - Excl01):</b> A waiting period of <b>36 Months</b> shall apply for any Pre-existing Disease declared at inception.", body_style))
        story1.append(Paragraph("4.3 <b>Specific Disease Waiting Period (Code - Excl02):</b> A waiting period of <b>24 Months</b> shall apply to the medical or surgical treatment of the following: Cataract, Hernia, Hydrocele, Piles, Fistula, Benign Prostatic Hypertrophy, Joint Replacement, Kidney Stones and Gallstones.", body_style))
        story1.append(Paragraph("4.4 <b>Permanent Exclusions:</b> Cosmetic or aesthetic surgery, dental treatment unless requiring hospitalization following accident, self-inflicted injuries, and non-prescribed alternative treatments are permanently excluded.", body_style))
        story1.append(Spacer(1, 10))
        
        # Table of benefits
        t_data1 = [
            ["Benefit Parameter", "Policy Terms (Optima Secure 2024)", "Page Reference"],
            ["Room Rent Limit", "Single Private Room (No Proportional Deduction)", "Page 2, Sec 3.1"],
            ["ICU Charges", "No Capping / Actuals up to Sum Insured", "Page 2, Sec 3.2"],
            ["Pre-Existing Disease Waiting", "36 Months", "Page 2, Sec 4.2"],
            ["Specific Ailments Waiting", "24 Months (Cataract, Hernia, Stones)", "Page 2, Sec 4.3"],
            ["Pre / Post Hospitalization", "60 Days Pre / 180 Days Post", "Page 1, Sec 2.2-2.3"],
            ["Co-Payment", "0% (Zero Co-payment across all ages)", "Page 2, Sec 3.1"]
        ]
        t1 = Table(t_data1, colWidths=[160, 260, 100])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTSIZE', (0,1), (-1,-1), 8.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story1.append(t1)
        doc1.build(story1)
        print("Generated sample PDF: HDFC_Optima_Secure_2024.pdf")

    # 2. Star Health Comprehensive 2024
    pdf_path_2 = policies_dir / "Star_Comprehensive_2024.pdf"
    if not pdf_path_2.exists():
        doc2 = SimpleDocTemplate(str(pdf_path_2), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story2 = []
        
        story2.append(Paragraph("Star Health and Allied Insurance Co. Ltd.", title_style))
        story2.append(Paragraph("<b>Policy Wording: Star Comprehensive Insurance Policy (Version 2024.2)</b>", h1_style))
        story2.append(Paragraph("Star Health Comprehensive Insurance Policy covers Inpatient Care, Day Care Procedures, and specified outpatient benefits subject to sub-limits and copays defined herein.", body_style))
        story2.append(Spacer(1, 10))
        
        story2.append(Paragraph("<b>SECTION 1: DEFINITIONS & COVERAGE</b>", h1_style))
        story2.append(Paragraph("1.1 <b>Inpatient Hospitalization:</b> Medical expenses incurred for hospitalization exceeding 24 hours.", body_style))
        story2.append(Paragraph("1.2 <b>Pre-Hospitalization Expenses:</b> Medical expenses incurred 30 days prior to admission.", body_style))
        story2.append(Paragraph("1.3 <b>Post-Hospitalization Expenses:</b> Medical expenses incurred 60 days following hospital discharge.", body_style))
        story2.append(Spacer(1, 10))
        
        story2.append(Paragraph("<b>SECTION 2: SUB-LIMITS & ROOM RENT CAPPING</b>", h1_style))
        story2.append(Paragraph("2.1 <b>Room Rent Capping:</b> Room Rent, boarding and nursing expenses are <b>Capped at 1% of Sum Insured per day</b>, subject to a maximum of ₹5,000/- per day.", body_style))
        story2.append(Paragraph("2.2 <b>Proportional Deduction Penalty:</b> If the Insured occupies a room category higher than 1% of Sum Insured, the Company shall effect a proportional deduction on all associated medical expenses including doctor consultation, surgical fees, OT charges, and specialist fees in proportion to the allowed room rent over actual room rent.", body_style))
        story2.append(Paragraph("2.3 <b>ICU Charges:</b> Capped at 2% of Sum Insured per day, subject to a maximum of ₹10,000/- per day.", body_style))
        story2.append(Paragraph("2.4 <b>Modern Robotic Surgeries:</b> Subject to a sub-limit of 50% of Sum Insured or maximum ₹2,50,000/- per policy period.", body_style))
        story2.append(PageBreak())
        
        # Page 2: Exclusions & Copays
        story2.append(Paragraph("<b>SECTION 3: WAITING PERIODS & CO-PAYMENTS</b>", h1_style))
        story2.append(Paragraph("3.1 <b>Initial 30-Day Waiting Period:</b> 30 days initial waiting period applies to all medical treatments.", body_style))
        story2.append(Paragraph("3.2 <b>Pre-Existing Disease Waiting Period (PED):</b> A mandatory waiting period of <b>48 Months</b> of continuous coverage applies for Pre-existing Diseases.", body_style))
        story2.append(Paragraph("3.3 <b>Specific Ailments Waiting Period:</b> A waiting period of <b>24 Months</b> applies for Cataract, Hernia, Hydrocele, Piles, Gallstones. Joint Replacement surgery is subject to a <b>48-Month waiting period</b>.", body_style))
        story2.append(Paragraph("3.4 <b>Mandatory Co-Payment:</b> A mandatory <b>10% Co-Payment</b> applies to each and every admissible claim for persons whose entry age is 61 years and above.", body_style))
        story2.append(Spacer(1, 10))
        
        t_data2 = [
            ["Benefit Parameter", "Policy Terms (Star Comprehensive 2024)", "Page Reference"],
            ["Room Rent Limit", "Capped at 1% of Sum Insured (Max ₹5,000/day)", "Page 1, Sec 2.1"],
            ["Proportional Deduction", "Applicable on all doctor & OT fees if room exceeded", "Page 1, Sec 2.2"],
            ["Pre-Existing Disease Waiting", "48 Months", "Page 2, Sec 3.2"],
            ["Specific Ailments Waiting", "24 Months (Joint Replacement 48 Months)", "Page 2, Sec 3.3"],
            ["Pre / Post Hospitalization", "30 Days Pre / 60 Days Post", "Page 1, Sec 1.2-1.3"],
            ["Co-Payment", "10% Co-pay for age 61+", "Page 2, Sec 3.4"]
        ]
        t2 = Table(t_data2, colWidths=[160, 260, 100])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#065f46")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTSIZE', (0,1), (-1,-1), 8.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story2.append(t2)
        doc2.build(story2)
        print("Generated sample PDF: Star_Comprehensive_2024.pdf")

    # 3. HDFC ERGO Optima Secure 2021 (Old Version for Policy Diffing)
    pdf_path_3 = policies_dir / "HDFC_Optima_Secure_2021_Old.pdf"
    if not pdf_path_3.exists():
        doc3 = SimpleDocTemplate(str(pdf_path_3), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story3 = []
        
        story3.append(Paragraph("HDFC ERGO General Insurance Company", title_style))
        story3.append(Paragraph("<b>Policy Wording: Optima Secure Plan (Version 2021.0 - Legacy)</b>", h1_style))
        story3.append(Paragraph("Legacy policy wording for previous coverage cycle.", body_style))
        story3.append(Spacer(1, 10))
        
        story3.append(Paragraph("<b>SECTION 2: SUB-LIMITS & ROOM RENT</b>", h1_style))
        story3.append(Paragraph("2.1 <b>Room Rent Limit:</b> Room rent capped at 1% of Sum Insured per day. Proportional deduction applicable if higher category occupied.", body_style))
        story3.append(Paragraph("2.2 <b>ICU Limit:</b> ICU capped at 2% of Sum Insured per day.", body_style))
        story3.append(Paragraph("2.3 <b>Modern Treatments:</b> Capped at ₹1,00,000 per policy year.", body_style))
        story3.append(Spacer(1, 10))
        
        story3.append(Paragraph("<b>SECTION 4: WAITING PERIODS & COPAY</b>", h1_style))
        story3.append(Paragraph("4.1 <b>Pre-Existing Disease Waiting Period:</b> Mandatory <b>48 Months</b> waiting period for Pre-existing Diseases.", body_style))
        story3.append(Paragraph("4.2 <b>Specific Illness Waiting Period:</b> 24 Months waiting period for Cataract, Hernia, Calculi.", body_style))
        story3.append(Paragraph("4.3 <b>Mandatory Co-Payment:</b> 10% co-payment applied across all claims.", body_style))
        doc3.build(story3)
        print("Generated sample PDF: HDFC_Optima_Secure_2021_Old.pdf")

if __name__ == "__main__":
    create_sample_policies()
