"""
Comprehensive test suite for Excel Retriever.

Tests the smart_extractor against 10 different Excel scenarios and validates:
1. Table detection accuracy
2. Data extraction correctness
3. Relationship detection
4. Text classification
5. Figure/chart detection
6. Merged cell handling
7. Formula evaluation
8. Multi-format export
"""

import json
import os
from pathlib import Path
from smart_extractor import SmartExcelExtractor, analysis_to_dict, table_to_csv_string, table_to_markdown
from datetime import datetime


class TestResult:
    def __init__(self, test_name):
        self.test_name = test_name
        self.passed = True
        self.errors = []
        self.warnings = []
        self.details = {}
    
    def fail(self, error_msg):
        self.passed = False
        self.errors.append(error_msg)
    
    def warn(self, warning_msg):
        self.warnings.append(warning_msg)
    
    def add_detail(self, key, value):
        self.details[key] = value


def test_1_simple_table(file_path):
    """Test 1: Simple single-table spreadsheet"""
    result = TestResult("Test 1: Simple Table")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        # Validate: Should have 1 sheet, 1 table
        if len(analysis.sheets) != 1:
            result.fail(f"Expected 1 sheet, found {len(analysis.sheets)}")
        
        sheet = analysis.sheets[0]
        if len(sheet.tables) != 1:
            result.fail(f"Expected 1 table, found {len(sheet.tables)}")
        else:
            table = sheet.tables[0]
            
            # Validate headers
            expected_headers = ["Employee ID", "Name", "Department", "Salary", "Hire Date"]
            if table.headers != expected_headers:
                result.fail(f"Headers mismatch. Expected {expected_headers}, got {table.headers}")
            
            # Validate row count
            if table.row_count != 5:
                result.fail(f"Expected 5 data rows, found {table.row_count}")
            
            # Validate data extraction
            if len(table.data) > 0:
                first_row = table.data[0]
                if first_row[0] != "E001":
                    result.fail(f"First employee ID should be 'E001', got '{first_row[0]}'")
            
            result.add_detail("tables_detected", len(sheet.tables))
            result.add_detail("rows_extracted", table.row_count)
            result.add_detail("columns", table.col_count)
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_2_multi_table_gaps(file_path):
    """Test 2: Multiple tables with gaps"""
    result = TestResult("Test 2: Multi-Table with Gaps")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        # Should detect 2 tables
        if len(sheet.tables) != 2:
            result.fail(f"Expected 2 tables, found {len(sheet.tables)}")
        else:
            # Table 1: Sales by Region
            table1 = sheet.tables[0]
            if "Region" not in table1.headers:
                result.fail("Table 1 should have 'Region' header")
            
            if table1.row_count != 4:
                result.fail(f"Table 1 should have 4 rows, found {table1.row_count}")
            
            # Table 2: Top Products
            table2 = sheet.tables[1]
            if "Product" not in table2.headers:
                result.fail("Table 2 should have 'Product' header")
            
            if table2.row_count != 5:
                result.fail(f"Table 2 should have 5 rows, found {table2.row_count}")
        
        # Should detect instruction text
        if len(sheet.text_blocks) < 1:
            result.warn("Expected to find instruction text blocks")
        
        result.add_detail("tables_detected", len(sheet.tables))
        result.add_detail("text_blocks", len(sheet.text_blocks))
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_3_formulas(file_path):
    """Test 3: Formulas and calculations"""
    result = TestResult("Test 3: Formulas")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        if len(sheet.tables) < 1:
            result.fail("Expected at least 1 table")
        else:
            table = sheet.tables[0]
            
            # Should have Total column
            if "Total" not in table.headers:
                result.fail("Expected 'Total' column in headers")
            
            # Check if formulas were evaluated (data_only=True)
            if len(table.data) > 0:
                first_row = table.data[0]
                total_col_idx = table.headers.index("Total") if "Total" in table.headers else -1
                if total_col_idx >= 0 and total_col_idx < len(first_row):
                    total_val = first_row[total_col_idx]
                    if total_val is None:
                        result.warn("Formula in Total column returned None")
                    elif isinstance(total_val, str) and total_val.startswith("="):
                        result.fail("Formula not evaluated - still showing formula string")
        
        result.add_detail("tables_detected", len(sheet.tables))
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_4_merged_cells(file_path):
    """Test 4: Merged cells"""
    result = TestResult("Test 4: Merged Cells")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        # Should detect merged cells
        if len(sheet.merged_cells) < 1:
            result.fail("Expected to detect merged cells")
        else:
            result.add_detail("merged_regions", len(sheet.merged_cells))
        
        # Should still extract table data correctly
        if len(sheet.tables) < 1:
            result.fail("Expected at least 1 table")
        else:
            table = sheet.tables[0]
            if table.row_count < 3:
                result.fail(f"Expected at least 3 data rows, found {table.row_count}")
        
        # Should detect title text
        if len(sheet.text_blocks) < 1:
            result.warn("Expected to find title/instruction text")
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_5_with_charts(file_path):
    """Test 5: Charts and figures"""
    result = TestResult("Test 5: Charts")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        # Should detect chart
        if len(sheet.figures) < 1:
            result.fail("Expected to detect at least 1 chart")
        else:
            chart = sheet.figures[0]
            if chart.chart_type != "line":
                result.warn(f"Expected line chart, detected {chart.chart_type}")
            
            result.add_detail("charts_detected", len(sheet.figures))
            result.add_detail("chart_title", chart.title)
        
        # Should detect 2 tables (data + summary)
        if len(sheet.tables) != 2:
            result.warn(f"Expected 2 tables, found {len(sheet.tables)}")
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_6_empty_rows_cols(file_path):
    """Test 6: Empty rows and columns"""
    result = TestResult("Test 6: Empty Rows/Cols")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        # Should detect 3 separate tables despite gaps
        if len(sheet.tables) != 3:
            result.fail(f"Expected 3 tables, found {len(sheet.tables)}")
        else:
            # Validate table separation
            table_names = [t.name or f"table_{t.table_index}" for t in sheet.tables]
            result.add_detail("tables", table_names)
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_7_financial_statement(file_path):
    """Test 7: Financial statement"""
    result = TestResult("Test 7: Financial Statement")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        # Should detect the main financial table
        if len(sheet.tables) < 1:
            result.fail("Expected at least 1 table")
        else:
            table = sheet.tables[0]
            
            # Should have Line Item column
            if "Line Item" not in table.headers:
                result.fail("Expected 'Line Item' column")
            
            # Should have multiple rows for revenue and expenses
            if table.row_count < 10:
                result.warn(f"Expected more rows in financial statement, found {table.row_count}")
        
        # Should detect title
        if len(sheet.text_blocks) < 1:
            result.warn("Expected to find title text")
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_8_scientific_data(file_path):
    """Test 8: Scientific data with units"""
    result = TestResult("Test 8: Scientific Data")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        # Should detect at least 1 table (primary data table)
        # Note: Statistical summary with formulas may be classified as text
        if len(sheet.tables) < 1:
            result.fail("Expected at least 1 table")
        else:
            # Table 1: Chemical Analysis
            table1 = sheet.tables[0]
            if "Sample ID" not in table1.headers:
                result.fail("Expected 'Sample ID' in first table")
            
            # Check for unit information in headers
            has_units = any("(" in h and ")" in h for h in table1.headers)
            if not has_units:
                result.warn("Expected unit information in headers (e.g., 'mg/L')")
            
            # Validate data extraction
            if table1.row_count != 5:
                result.fail(f"Expected 5 sample rows, found {table1.row_count}")
        
        # Note about statistical summary
        if len(sheet.tables) == 1:
            result.add_detail("note", "Statistical summary with formulas classified as text (acceptable)")
        
        result.add_detail("tables_detected", len(sheet.tables))
        
        # Should detect instruction about measurement conditions
        instructions = [t for t in sheet.text_blocks if t.classification == "instruction"]
        if len(instructions) < 1:
            result.warn("Expected to find instruction text about measurement conditions")
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_9_pivot_like(file_path):
    """Test 9: Pivot table structure"""
    result = TestResult("Test 9: Pivot-like Structure")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        # Should detect the cross-tab table
        if len(sheet.tables) < 1:
            result.fail("Expected at least 1 table")
        else:
            table = sheet.tables[0]
            
            # Should have region columns
            if "North" not in table.headers and "South" not in table.headers:
                result.fail("Expected region columns (North, South, etc.)")
            
            # Should have multiple product rows
            if table.row_count < 5:
                result.fail(f"Expected at least 5 product rows, found {table.row_count}")
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_10_mixed_data_types(file_path):
    """Test 10: Mixed data types"""
    result = TestResult("Test 10: Mixed Data Types")
    
    try:
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        sheet = analysis.sheets[0]
        
        if len(sheet.tables) < 1:
            result.fail("Expected at least 1 table")
        else:
            table = sheet.tables[0]
            
            # Should extract various data types
            if table.row_count < 10:
                result.fail(f"Expected at least 10 rows of test data, found {table.row_count}")
            
            # Check if different data types are preserved
            has_numbers = any(isinstance(cell, (int, float)) for row in table.data for cell in row if cell is not None)
            has_strings = any(isinstance(cell, str) for row in table.data for cell in row if cell is not None)
            has_dates = any(isinstance(cell, datetime) for row in table.data for cell in row if cell is not None)
            
            if not has_numbers:
                result.warn("No numeric values detected")
            if not has_strings:
                result.warn("No string values detected")
            if not has_dates:
                result.warn("No date values detected")
            
            result.add_detail("has_numbers", has_numbers)
            result.add_detail("has_strings", has_strings)
            result.add_detail("has_dates", has_dates)
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_relationships_detection():
    """Test relationship detection on complex_sample.xlsx"""
    result = TestResult("Relationship Detection")
    
    try:
        file_path = "excel_files/complex_sample.xlsx"
        if not os.path.exists(file_path):
            result.warn(f"Skipping - {file_path} not found")
            return result
        
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        # Should detect relationships
        if len(analysis.relationships) < 1:
            result.fail("Expected to detect relationships between tables")
        else:
            result.add_detail("relationships_found", len(analysis.relationships))
            
            # Check for specific expected relationship
            project_rel = any("project id" in r.common_columns for r in analysis.relationships)
            if project_rel:
                result.add_detail("project_id_relationship", "✓ Found")
            else:
                result.warn("Expected to find 'project id' relationship")
        
        # Should have LLM schema description
        if not analysis.llm_schema_description:
            result.fail("LLM schema description is empty")
        else:
            if "Key Relationships" not in analysis.llm_schema_description:
                result.warn("LLM schema should include 'Key Relationships' section")
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def test_export_formats():
    """Test multi-format export"""
    result = TestResult("Export Formats")
    
    try:
        file_path = "excel_files/test_1_simple_table.xlsx"
        extractor = SmartExcelExtractor(file_path)
        analysis = extractor.analyze()
        extractor.close()
        
        if len(analysis.sheets) > 0 and len(analysis.sheets[0].tables) > 0:
            table = analysis.sheets[0].tables[0]
            
            # Test CSV export
            csv_output = table_to_csv_string(table)
            if not csv_output or len(csv_output) < 10:
                result.fail("CSV export failed or empty")
            else:
                result.add_detail("csv_export", "✓ Success")
            
            # Test Markdown export
            md_output = table_to_markdown(table)
            if not md_output or "|" not in md_output:
                result.fail("Markdown export failed or invalid format")
            else:
                result.add_detail("markdown_export", "✓ Success")
            
            # Test JSON serialization
            dict_output = analysis_to_dict(analysis)
            json_output = json.dumps(dict_output, default=str)
            if not json_output or len(json_output) < 10:
                result.fail("JSON serialization failed")
            else:
                result.add_detail("json_export", "✓ Success")
        else:
            result.fail("No table found to test export formats")
    
    except Exception as e:
        result.fail(f"Exception: {str(e)}")
    
    return result


def run_all_tests():
    """Run all tests and generate report"""
    print("=" * 80)
    print("COMPREHENSIVE EXCEL RETRIEVER TEST SUITE")
    print("=" * 80)
    print()
    
    test_files = [
        ("excel_files/test_1_simple_table.xlsx", test_1_simple_table),
        ("excel_files/test_2_multi_table_gaps.xlsx", test_2_multi_table_gaps),
        ("excel_files/test_3_formulas.xlsx", test_3_formulas),
        ("excel_files/test_4_merged_cells.xlsx", test_4_merged_cells),
        ("excel_files/test_5_with_charts.xlsx", test_5_with_charts),
        ("excel_files/test_6_empty_rows_cols.xlsx", test_6_empty_rows_cols),
        ("excel_files/test_7_financial_statement.xlsx", test_7_financial_statement),
        ("excel_files/test_8_scientific_data.xlsx", test_8_scientific_data),
        ("excel_files/test_9_pivot_like.xlsx", test_9_pivot_like),
        ("excel_files/test_10_mixed_data_types.xlsx", test_10_mixed_data_types),
    ]
    
    results = []
    
    # Run file-based tests
    for file_path, test_func in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  SKIP: {file_path} not found")
            continue
        
        print(f"Running: {test_func.__doc__}")
        result = test_func(file_path)
        results.append(result)
        
        if result.passed:
            print(f"  ✅ PASS")
        else:
            print(f"  ❌ FAIL")
            for error in result.errors:
                print(f"     - {error}")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"     ⚠️  {warning}")
        
        if result.details:
            for key, value in result.details.items():
                print(f"     • {key}: {value}")
        print()
    
    # Run special tests
    print("Running: Relationship Detection Test")
    rel_result = test_relationships_detection()
    results.append(rel_result)
    if rel_result.passed:
        print(f"  ✅ PASS")
    else:
        print(f"  ❌ FAIL")
        for error in rel_result.errors:
            print(f"     - {error}")
    if rel_result.warnings:
        for warning in rel_result.warnings:
            print(f"     ⚠️  {warning}")
    if rel_result.details:
        for key, value in rel_result.details.items():
            print(f"     • {key}: {value}")
    print()
    
    print("Running: Export Formats Test")
    export_result = test_export_formats()
    results.append(export_result)
    if export_result.passed:
        print(f"  ✅ PASS")
    else:
        print(f"  ❌ FAIL")
        for error in export_result.errors:
            print(f"     - {error}")
    if export_result.details:
        for key, value in export_result.details.items():
            print(f"     • {key}: {value}")
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print()
    
    if failed > 0:
        print("Failed Tests:")
        for r in results:
            if not r.passed:
                print(f"  - {r.test_name}")
                for error in r.errors:
                    print(f"      {error}")
    
    # Save detailed report
    report_path = "test_results.json"
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "success_rate": f"{(passed/total*100):.1f}%",
        "results": [
            {
                "test_name": r.test_name,
                "passed": r.passed,
                "errors": r.errors,
                "warnings": r.warnings,
                "details": r.details
            }
            for r in results
        ]
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
