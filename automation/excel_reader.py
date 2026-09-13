import os
from openpyxl import load_workbook
from models import TestCase
from config import EXCEL_FILE

REQUIRED_COLUMNS = [
    "Test ID",
    "Test Name",
    "Category",
    "Steps",
    "Expected Result",
    "Status",
    "AI Observation"
]

def load_test_cases() -> list[TestCase]:
    if not os.path.exists(EXCEL_FILE):
        raise FileNotFoundError(f"Excel file not found at {EXCEL_FILE}")

    wb = load_workbook(EXCEL_FILE)
    sheet = wb.active

    headers = [cell.value for cell in sheet[1]]
    
    for col in REQUIRED_COLUMNS:
        if col not in headers:
            raise ValueError(f"Missing required column: {col}")

    col_indices = {col: headers.index(col) for col in REQUIRED_COLUMNS}
    test_cases = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        test_id = row[col_indices["Test ID"]]
        if not test_id:
            continue
            
        test_case = TestCase(
            test_id=str(test_id),
            test_name=str(row[col_indices["Test Name"]]),
            category=str(row[col_indices["Category"]]),
            raw_steps=str(row[col_indices["Steps"]]),
            expected_result=str(row[col_indices["Expected Result"]]),
            status=str(row[col_indices["Status"]] or "NOT RUN"),
            ai_observation=str(row[col_indices["AI Observation"]]) if row[col_indices["AI Observation"]] else None
        )
        test_cases.append(test_case)

    return test_cases
