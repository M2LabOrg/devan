"""
Sample PDF Generator for Prompt MCP Demo

This script creates sample PDF files for testing the MCP server.
These are simple text-based PDFs that simulate real engineering reports and proposals.
"""

import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation will be skipped.")
    print("Install with: uv add reportlab")


def create_sample_pdfs(output_dir: str = "../pdf_files"):
    """Create sample PDF files for demonstration."""
    
    if not REPORTLAB_AVAILABLE:
        print("Cannot create PDFs - reportlab not available")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create offshore wind assessment report
    create_offshore_wind_report(output_dir)
    
    # Create pipeline safety proposal
    create_pipeline_proposal(output_dir)
    
    # Create technical memorandum
    create_technical_memo(output_dir)
    
    print(f"\nAll sample PDFs created in: {output_dir}")


def create_offshore_wind_report(output_dir: str):
    """Create an offshore wind farm assessment report."""
    
    filepath = os.path.join(output_dir, "offshore_wind_assessment.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        spaceAfter=10
    )
    
    story = []
    
    # Title
    story.append(Paragraph("OFFSHORE WIND FARM ASSESSMENT REPORT", title_style))
    story.append(Paragraph("North Sea Project Alpha - Phase 1 Evaluation", styles['Heading3']))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary content
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    story.append(Paragraph("""
    This report presents the findings of the independent assessment of the proposed 
    North Sea offshore wind farm development. The assessment covers technical feasibility, 
    environmental impact, and operational safety considerations for the 500MW installation.
    """, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Key Findings:", heading_style))
    findings = [
        "The proposed turbine layout demonstrates optimal energy capture with minimal wake effects.",
        "Foundation design meets all structural requirements for North Sea conditions.",
        "Environmental impact assessment shows acceptable marine ecosystem disruption.",
        "Grid connection infrastructure requires reinforcement at substation level.",
        "Operations and maintenance strategy is well-conceived for harsh weather conditions."
    ]
    for finding in findings:
        story.append(Paragraph(f"• {finding}", body_style))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(PageBreak())
    
    # Technical Analysis
    story.append(Paragraph("TECHNICAL ANALYSIS", heading_style))
    story.append(Paragraph("""
    The technical evaluation covered turbine performance, foundation integrity, and
    electrical system design. The analysis confirms compliance with IEC 61400-3-1 standards
    and applicable ISO 19901-1 guidelines for offshore wind turbines.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Turbine Performance Assessment", heading_style))
    story.append(Paragraph("""
    The selected 15MW turbines demonstrate excellent power curves and availability 
    projections. Annual energy production estimates of 2.1 TWh align with industry 
    benchmarks for similar North Sea installations. Wake modeling indicates 8-12% 
    array losses, consistent with the empirical database.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Foundation and Substructure", heading_style))
    story.append(Paragraph("""
    Monopile foundations are appropriately sized for water depths of 25-35 meters. 
    Scour protection design accounts for North Sea sediment conditions. Fatigue 
    analysis shows 25-year design life compliance with adequate safety margins.
    """, body_style))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(PageBreak())
    
    # Environmental Assessment
    story.append(Paragraph("ENVIRONMENTAL IMPACT ASSESSMENT", heading_style))
    story.append(Paragraph("""
    The environmental evaluation addressed marine mammals, seabirds, benthic habitats, 
    and fishing interests. The assessment methodology follows OSPAR guidelines and 
    UK Marine Policy Statement requirements.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Marine Ecology", heading_style))
    story.append(Paragraph("""
    Pile driving activities pose temporary disturbance to harbor porpoise populations. 
    Recommended mitigation includes double bubble curtains and soft-start protocols. 
    Long-term habitat monitoring program should track benthic community recovery.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Recommendations", heading_style))
    story.append(Paragraph("""
    Based on this comprehensive assessment, The assessment recommends proceeding with the 
    North Sea Project Alpha development, subject to implementation of the identified 
    risk mitigation measures and ongoing monitoring commitments outlined in this report.
    """, body_style))
    
    doc.build(story)
    print(f"Created: {filepath}")


def create_pipeline_proposal(output_dir: str):
    """Create a pipeline safety proposal."""
    
    filepath = os.path.join(output_dir, "pipeline_safety_proposal.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        spaceAfter=10,
        spaceBefore=10
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=8
    )
    
    story = []
    
    # Title
    story.append(Paragraph("PROPOSAL FOR PIPELINE SAFETY ASSESSMENT", title_style))
    story.append(Paragraph("Client: Gulf Coast Energy Partners", styles['Heading3']))
    story.append(Paragraph("Date: March 2024", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Introduction
    story.append(Paragraph("INTRODUCTION", heading_style))
    story.append(Paragraph("""
    Gulf Coast Energy Partners has engaged M2Lab Engineering to conduct a comprehensive safety 
    assessment of the proposed 200km subsea natural gas pipeline connecting offshore 
    production platforms to onshore processing facilities. This proposal outlines 
    M2Lab Engineering's approach, methodology, and deliverables for this critical infrastructure project.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Project Background", heading_style))
    story.append(Paragraph("""
    The Gulf Star Pipeline will transport up to 500 million cubic feet per day of 
    natural gas from the Starfish Platform in 150m water depth to the Port Arthur 
    processing terminal. Pipeline design pressure is 150 bar with operating temperature 
    range of 5-45°C.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(PageBreak())
    
    # Scope of Work
    story.append(Paragraph("SCOPE OF WORK", heading_style))
    story.append(Paragraph("M2Lab Engineering will perform the following assessments:", body_style))
    
    scope_items = [
        "HAZID (Hazard Identification) workshop and documentation",
        "Pipeline routing and geohazard assessment",
        "Material selection and corrosion engineering review",
        "Installation methodology safety evaluation",
        "Emergency shutdown and isolation system design review",
        "Leak detection system specification validation",
        "Safety management system framework development"
    ]
    
    for item in scope_items:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Deliverables", heading_style))
    story.append(Paragraph("""
    The assessment will produce a comprehensive safety case document suitable for 
    regulatory submission to BSEE and PHMSA. Additional deliverables include 
    technical memos for each assessment area, risk register, and compliance matrix.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(PageBreak())
    
    # Approach
    story.append(Paragraph("ENGINEERING APPROACH", heading_style))
    story.append(Paragraph("""
    Our methodology integrates ASME B31.8 for pipeline integrity, API RP 1111 for
    submarine pipeline systems, and ISO 17776 for offshore safety management.
    The assessment will follow a risk-based approach aligned with API RP 75 safety 
    and environmental management system principles.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Team Composition", heading_style))
    story.append(Paragraph("""
    M2Lab Engineering will assign a multi-disciplinary team including subsea pipeline engineers, 
    safety specialists, materials scientists, and regulatory compliance experts. 
    All team members hold relevant certifications and have minimum 10 years offshore 
    industry experience.
    """, body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Timeline and Budget", heading_style))
    story.append(Paragraph("""
    The assessment will be completed within 16 weeks from contract award. The proposed 
    budget reflects M2Lab Engineering's commitment to delivering thorough, independent assessment 
    while maintaining cost efficiency for this critical Gulf Coast infrastructure project.
    """, body_style))
    
    doc.build(story)
    print(f"Created: {filepath}")


def create_technical_memo(output_dir: str):
    """Create a technical memorandum."""
    
    filepath = os.path.join(output_dir, "fatigue_analysis_memo.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=8
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=8
    )
    
    story = []
    
    # Header
    story.append(Paragraph("TECHNICAL MEMORANDUM", title_style))
    story.append(Paragraph("Subject: Fatigue Analysis Update - Platform Bravo", heading_style))
    story.append(Paragraph("To: Project Engineering Manager", body_style))
    story.append(Paragraph("From: M2Lab Structural Engineering Team", body_style))
    story.append(Paragraph("Date: 15 March 2024", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Purpose
    story.append(Paragraph("PURPOSE", heading_style))
    story.append(Paragraph("""
    This memorandum presents updated fatigue life calculations for the Platform Bravo 
    jacket structure following recent metocean data revision. The analysis incorporates 
    2023 wave scatter diagram updates and revised current profiles from ADCP measurements.
    """, body_style))
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("BACKGROUND", heading_style))
    story.append(Paragraph("""
    Platform Bravo, installed in 1998, operates in 82m water depth in the North Sea. 
    The eight-leg jacket structure supports a topsides weight of 12,500 tonnes. Original 
    design fatigue life was 25 years with Safety Factor 10 on S-N curves.
    """, body_style))
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("METHODOLOGY", heading_style))
    story.append(Paragraph("""
    M2Lab Engineering performed spectral fatigue analysis using SESAM software with updated
    environmental loading per ISO 19902 (2020). Wave loading calculated using
    MacCamy-Fuchs diffraction theory. Hot spot stress concentration factors from
    previous FE analysis validated against ISO 19902 recommendations.
    """, body_style))
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("RESULTS", heading_style))
    story.append(Paragraph("""
    Updated analysis indicates accumulated fatigue damage of 0.42 at critical 
    connections (leg-brace joints B2 and C3). Remaining fatigue life calculated 
    as 14.3 years at current operational loading. This exceeds the platform's 
    intended service life through 2035.
    """, body_style))
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("RECOMMENDATIONS", heading_style))
    story.append(Paragraph("""
    1. Continue routine NDT inspection of identified critical joints at 3-year intervals.
    2. Implement strain monitoring at joints B2 and C3 for real-time fatigue tracking.
    3. Reassess if significant production changes or severe storm events occur.
    4. Plan detailed reassessment in 2030 as platform approaches end of design life.
    """, body_style))
    
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("CONCLUSION", heading_style))
    story.append(Paragraph("""
    The Platform Bravo jacket structure demonstrates adequate fatigue life for continued 
    operation through the planned service period. Updated environmental data does not 
    materially affect previous assessments. Recommended monitoring and inspection 
    programs ensure ongoing structural integrity.
    """, body_style))
    
    doc.build(story)
    print(f"Created: {filepath}")


if __name__ == "__main__":
    create_sample_pdfs()
