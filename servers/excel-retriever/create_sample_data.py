#!/usr/bin/env python3
"""
Create sample Excel files for testing the Excel Retriever MCP Server.
Run this script to generate test data before the demo.
"""

import pandas as pd
import os


def create_sample_excel_files(output_dir: str = "excel_files"):
    """Create sample Excel files with project data."""

    os.makedirs(output_dir, exist_ok=True)

    # Sample data - Offshore Projects
    projects_data = {
        'Project_ID': ['PRJ-001', 'PRJ-002', 'PRJ-003', 'PRJ-004', 'PRJ-005'],
        'Project_Name': [
            'Offshore Platform A',
            'Wind Farm B - Phase 1',
            'Subsea Pipeline C',
            'Refinery Upgrade D',
            'FPSO Installation E'
        ],
        'Region': ['North Sea', 'Baltic Sea', 'Gulf of Mexico', 'Middle East', 'Norwegian Sea'],
        'Start_Date': ['2023-01-15', '2023-03-20', '2022-11-10', '2024-01-05', '2024-06-01'],
        'End_Date': ['2024-06-30', '2025-12-31', '2024-03-15', '2026-06-30', '2025-09-30'],
        'Budget_MUSD': [450.5, 280.3, 125.8, 890.2, 340.7],
        'Actual_Cost_MUSD': [445.2, 295.1, 118.5, 920.5, 338.9],
        'Status': ['Complete', 'In Progress', 'Complete', 'In Progress', 'Planning'],
        'Risk_Level': ['Low', 'Medium', 'Low', 'High', 'Medium']
    }
    
    # Create Excel file with multiple sheets
    file_path = os.path.join(output_dir, "sample_projects.xlsx")
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # Sheet 1: Projects
        df_projects = pd.DataFrame(projects_data)
        df_projects.to_excel(writer, sheet_name='Projects', index=False)
        
        # Sheet 2: Summary
        total_budget = sum(projects_data['Budget_MUSD'])
        total_actual = sum(projects_data['Actual_Cost_MUSD'])
        
        summary_data = {
            'Metric': [
                'Total Projects',
                'Total Budget (MUSD)',
                'Total Actual Cost (MUSD)',
                'Budget Variance (MUSD)',
                'Projects Complete',
                'Projects In Progress',
                'Projects Planning'
            ],
            'Value': [
                len(projects_data['Project_ID']),
                round(total_budget, 2),
                round(total_actual, 2),
                round(total_actual - total_budget, 2),
                projects_data['Status'].count('Complete'),
                projects_data['Status'].count('In Progress'),
                projects_data['Status'].count('Planning')
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 3: Risk Analysis
        risk_levels = ['Low', 'Medium', 'High']
        risk_data = []
        for risk in risk_levels:
            count = projects_data['Risk_Level'].count(risk)
            budget = sum([
                projects_data['Budget_MUSD'][i]
                for i, r in enumerate(projects_data['Risk_Level'])
                if r == risk
            ])
            risk_data.append({
                'Risk_Level': risk,
                'Project_Count': count,
                'Total_Budget_MUSD': budget,
                'Percentage': round(count / len(projects_data['Project_ID']) * 100, 1)
            })
        pd.DataFrame(risk_data).to_excel(writer, sheet_name='Risk_Analysis', index=False)
        
        # Sheet 4: Regional Breakdown
        regions = list(set(projects_data['Region']))
        region_data = []
        for region in regions:
            region_projects = [
                i for i, r in enumerate(projects_data['Region'])
                if r == region
            ]
            region_data.append({
                'Region': region,
                'Project_Count': len(region_projects),
                'Total_Budget_MUSD': sum([
                    projects_data['Budget_MUSD'][i] for i in region_projects
                ]),
                'Avg_Project_Budget_MUSD': sum([
                    projects_data['Budget_MUSD'][i] for i in region_projects
                ]) / len(region_projects) if region_projects else 0
            })
        pd.DataFrame(region_data).to_excel(writer, sheet_name='Regional', index=False)
    
    print(f"✓ Created: {file_path}")
    print(f"  Sheets: Projects, Summary, Risk_Analysis, Regional")
    
    # Create second sample file - Equipment Inventory
    equipment_data = {
        'Equipment_ID': ['EQ-1001', 'EQ-1002', 'EQ-1003', 'EQ-1004', 'EQ-1005'],
        'Equipment_Name': [
            'Hydraulic Crane 50T',
            'Welding Robot X200',
            'CNC Milling Center',
            'Pressure Vessel 1000L',
            'Generator 500kW'
        ],
        'Category': ['Lifting', 'Welding', 'Machining', 'Pressure', 'Power'],
        'Purchase_Date': ['2019-03-15', '2021-07-20', '2020-11-10', '2018-05-22', '2022-02-01'],
        'Cost_MUSD': [1.2, 0.8, 2.5, 0.6, 1.8],
        'Location': ['Yard A', 'Shop B', 'Shop B', 'Yard C', 'Yard A'],
        'Status': ['Active', 'Active', 'Maintenance', 'Active', 'Active'],
        'Next_Inspection': ['2025-03-15', '2025-07-20', '2025-01-10', '2025-05-22', '2025-08-01']
    }
    
    equip_file = os.path.join(output_dir, "equipment_inventory.xlsx")
    with pd.ExcelWriter(equip_file, engine='openpyxl') as writer:
        pd.DataFrame(equipment_data).to_excel(writer, sheet_name='Equipment', index=False)
        
        # Add maintenance schedule
        maint_data = {
            'Equipment_ID': ['EQ-1001', 'EQ-1002', 'EQ-1003', 'EQ-1004', 'EQ-1005'],
            'Last_Maintenance': ['2024-03-15', '2024-07-20', '2024-11-01', '2024-05-22', '2024-08-01'],
            'Next_Maintenance': ['2025-03-15', '2025-07-20', '2025-01-15', '2025-05-22', '2025-08-01'],
            'Maintenance_Type': ['Annual', 'Annual', 'Repair', 'Annual', 'Annual'],
            'Cost_KUSD': [15, 12, 45, 8, 20]
        }
        pd.DataFrame(maint_data).to_excel(writer, sheet_name='Maintenance', index=False)
    
    print(f"✓ Created: {equip_file}")
    print(f"  Sheets: Equipment, Maintenance")
    print(f"\n✓ All sample files created in: {output_dir}/")


if __name__ == "__main__":
    create_sample_excel_files()
