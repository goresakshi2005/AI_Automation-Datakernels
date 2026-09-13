def parse_step(raw_step: str) -> dict:
    """
    Parses a single machine-readable step into a dictionary.
    Examples:
    "OPEN: /" -> {"command": "OPEN", "target": "/"}
    "FILL: email-input = john@example.com" -> {"command": "FILL", "target": "email-input", "value": "john@example.com"}
    "CLICK: search-button" -> {"command": "CLICK", "target": "search-button"}
    """
    if not raw_step or not raw_step.strip():
        return {}

    parts = raw_step.split(":", 1)
    command = parts[0].strip().upper()
    
    if len(parts) < 2:
        return {"command": command}
        
    target_part = parts[1].strip()
    
    # Check if there's a value component for FILL or ASSERT_TEXT
    if command == "FILL" and "=" in target_part:
        t_parts = target_part.split("=", 1)
        target = t_parts[0].strip()
        value = t_parts[1].strip()
        return {"command": command, "target": target, "value": value}
    elif command == "ASSERT_TEXT" and " CONTAINS " in target_part:
        t_parts = target_part.split(" CONTAINS ", 1)
        target = t_parts[0].strip()
        value = t_parts[1].strip()
        return {"command": command, "target": target, "value": value}
        
    return {"command": command, "target": target_part}
