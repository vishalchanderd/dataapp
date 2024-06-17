import re

def create_table_name_from_filename(filename):
    # Replace invalid characters (like hyphens) with an underscore
    table_name = re.sub(r"[^a-zA-Z0-9_]", "_", filename)
    
    # Ensure the table name starts with a valid character (use 'T' prefix if not)
    if not re.match(r"^[a-zA-Z_]", table_name):
        table_name = "T" + table_name
    
    # Optionally, truncate to meet max length requirements (e.g., 128 characters for SQL Server)
    max_length = 128
    table_name = table_name[:max_length]
    
    # Remove trailing underscores which might be added after cleaning
    table_name = table_name.rstrip("_")
    
    return table_name