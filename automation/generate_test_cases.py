import os
from openpyxl import Workbook
from config import EXCEL_FILE, TEST_CASES_DIR

def write_test_cases():
    os.makedirs(TEST_CASES_DIR, exist_ok=True)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Test Cases"
    
    headers = [
        "Test ID", "Test Name", "Category", "Steps", 
        "Expected Result", "Status", "AI Observation"
    ]
    ws.append(headers)
    
    tc_001_steps = """OPEN: /
FILL: city-input = New York
FILL: checkin-input = 2026-09-20
FILL: checkout-input = 2026-09-23
FILL: guests-input = 2
CLICK: search-button
WAIT_FOR: room-card-1
CLICK: view-details-1
WAIT_FOR: room-name
CLICK: book-now-button
WAIT_FOR: first-name-input
FILL: first-name-input = John
FILL: last-name-input = Doe
FILL: email-input = john@example.com
FILL: phone-input = 9876543210
FILL: booking-checkin-input = 2026-09-20
FILL: booking-checkout-input = 2026-09-23
FILL: booking-guests-input = 2
FILL: special-requests-input = No special requests
FILL: card-number-input = 4111111111111111
FILL: expiry-input = 12/30
FILL: cvv-input = 123
CLICK: confirm-booking-button
WAIT_FOR: booking-confirmation
ASSERT_VISIBLE: booking-confirmation
ASSERT_TEXT: booking-reference CONTAINS BK-
SCREENSHOT: TC-001_step-26_success"""

    tc_002_steps = """OPEN: /
FILL: city-input = New York
FILL: checkin-input = 2026-09-20
FILL: checkout-input = 2026-09-23
FILL: guests-input = 2
CLICK: search-button
WAIT_FOR: room-card-1
ASSERT_VISIBLE: room-card-1
SCREENSHOT: TC-002_step-08_success"""

    tc_003_steps = """OPEN: /
FILL: city-input = New York
FILL: checkin-input = 2026-09-20
FILL: checkout-input = 2026-09-23
FILL: guests-input = 2
CLICK: search-button
WAIT_FOR: room-card-1
CLICK: view-details-1
WAIT_FOR: room-name
ASSERT_VISIBLE: room-name
ASSERT_VISIBLE: room-type
ASSERT_VISIBLE: room-price
SCREENSHOT: TC-003_step-12_success"""

    tc_004_steps = """OPEN: /
FILL: city-input = New York
FILL: checkin-input = 2026-09-20
FILL: checkout-input = 2026-09-23
FILL: guests-input = 2
CLICK: search-button
WAIT_FOR: room-card-1
CLICK: view-details-1
WAIT_FOR: room-name
CLICK: book-now-button
WAIT_FOR: first-name-input
FILL: first-name-input = John
FILL: last-name-input = Doe
FILL: email-input = john@example.com
FILL: phone-input = 9876543210
FILL: booking-checkin-input = 2026-09-20
FILL: booking-checkout-input = 2026-09-23
FILL: booking-guests-input = 2
FILL: card-number-input = 4111111111111111
FILL: expiry-input = 12/30
FILL: cvv-input = 123
CLICK: confirm-booking-button
WAIT_FOR: booking-confirmation
OPEN: /bookings
WAIT_FOR: booking-card-1
ASSERT_VISIBLE: booking-card-1
SCREENSHOT: TC-004_step-26_success"""

    base_validation_prefix = """OPEN: /
FILL: city-input = New York
FILL: checkin-input = 2026-09-20
FILL: checkout-input = 2026-09-23
FILL: guests-input = 2
CLICK: search-button
WAIT_FOR: room-card-1
CLICK: view-details-1
WAIT_FOR: room-name
CLICK: book-now-button
WAIT_FOR: first-name-input
FILL: first-name-input = John
FILL: last-name-input = Doe
FILL: email-input = john@example.com
FILL: phone-input = 9876543210
FILL: booking-checkin-input = 2026-09-20
FILL: booking-checkout-input = 2026-09-23
FILL: booking-guests-input = 2
FILL: card-number-input = 4111111111111111
FILL: expiry-input = 12/30
FILL: cvv-input = 123\n"""

    def generate_validation_test(field_to_override: str, override_value: str, error_test_id: str) -> str:
        lines = base_validation_prefix.strip().split("\n")
        new_lines = []
        for line in lines:
            if line.startswith(f"FILL: {field_to_override} ="):
                if override_value == "":
                    new_lines.append(f"FILL: {field_to_override} =")
                else:
                    new_lines.append(f"FILL: {field_to_override} = {override_value}")
            else:
                new_lines.append(line)
        new_lines.append("CLICK: confirm-booking-button")
        new_lines.append(f"WAIT_FOR: {error_test_id}")
        new_lines.append(f"ASSERT_VISIBLE: {error_test_id}")
        new_lines.append("SCREENSHOT: validation_error")
        return "\n".join(new_lines)

    tc_005_steps = generate_validation_test("first-name-input", "", "first-name-error")
    tc_006_steps = generate_validation_test("last-name-input", "", "last-name-error")
    tc_007_steps = generate_validation_test("email-input", "invalid-email", "email-error")
    tc_008_steps = generate_validation_test("phone-input", "abcdefghij", "phone-error")
    tc_009_steps = generate_validation_test("phone-input", "12345", "phone-error")
    tc_010_steps = generate_validation_test("booking-checkout-input", "2026-09-18", "booking-checkout-error")
    tc_011_steps = generate_validation_test("booking-guests-input", "0", "booking-guests-error")
    tc_012_steps = generate_validation_test("booking-guests-input", "11", "booking-guests-error")
    tc_013_steps = generate_validation_test("card-number-input", "1234", "card-error")
    tc_014_steps = generate_validation_test("expiry-input", "10/20", "expiry-error") # hardcoded expired date
    tc_015_steps = generate_validation_test("cvv-input", "12", "cvv-error")


    tests = [
        ("TC-001", "Complete valid booking flow", "Happy Path", tc_001_steps, "Booking confirmation displayed"),
        ("TC-002", "Search for available rooms", "Happy Path", tc_002_steps, "Available rooms are displayed"),
        ("TC-003", "View room details", "Happy Path", tc_003_steps, "Room details are displayed"),
        ("TC-004", "View my bookings", "Happy Path", tc_004_steps, "User bookings are displayed"),
        ("TC-005", "Empty first name", "Validation", tc_005_steps, "First name validation error is displayed"),
        ("TC-006", "Empty last name", "Validation", tc_006_steps, "Last name validation error is displayed"),
        ("TC-007", "Invalid email format", "Validation", tc_007_steps, "Email validation error is displayed"),
        ("TC-008", "Invalid phone (letters)", "Validation", tc_008_steps, "Phone validation error is displayed"),
        ("TC-009", "Phone less than 10 digits", "Validation", tc_009_steps, "Phone length validation error is displayed"),
        ("TC-010", "Check-out before check-in", "Validation", tc_010_steps, "Check-out validation error is displayed"),
        ("TC-011", "Guests = 0", "Validation", tc_011_steps, "Guests min validation error is displayed"),
        ("TC-012", "Guests > 10", "Validation", tc_012_steps, "Guests max validation error is displayed"),
        ("TC-013", "Invalid card number", "Validation", tc_013_steps, "Card length validation error is displayed"),
        ("TC-014", "Expired card date", "Validation", tc_014_steps, "Expiry validation error is displayed"),
        ("TC-015", "Invalid CVV", "Validation", tc_015_steps, "CVV validation error is displayed"),
    ]

    for t in tests:
        ws.append([t[0], t[1], t[2], t[3], t[4], "NOT RUN", ""])
        
    wb.save(EXCEL_FILE)
    print(f"Generated {EXCEL_FILE} successfully.")

if __name__ == "__main__":
    write_test_cases()
