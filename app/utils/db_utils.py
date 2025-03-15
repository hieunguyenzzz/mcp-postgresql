from app.models.dynamic import get_all_tables_info, get_table_info, execute_query

def get_db_schema_description():
    """
    Generate a text description of the database schema for the LLM.
    """
    tables_info = get_all_tables_info()
    description = "Database Schema:\n\n"
    
    for table_name, table_info in tables_info.items():
        description += f"Table: {table_name}\n"
        description += "Columns:\n"
        
        for column in table_info['columns']:
            pk_marker = " (Primary Key)" if column['primary_key'] else ""
            nullable = "NULL" if column['nullable'] else "NOT NULL"
            default = f" DEFAULT {column['default']}" if column['default'] is not None else ""
            description += f"  - {column['name']}: {column['type']} {nullable}{default}{pk_marker}\n"
        
        if table_info['foreign_keys']:
            description += "Foreign Keys:\n"
            for fk in table_info['foreign_keys']:
                constrained = ", ".join(fk['constrained_columns'])
                referred = ", ".join(fk['referred_columns'])
                description += f"  - {constrained} -> {fk['referred_table']}({referred})\n"
        
        description += "\n"
    
    return description

def get_table_sample_data(table_name, limit=5):
    """
    Get sample data from a table to provide context to the LLM.
    """
    table_info = get_table_info(table_name)
    if not table_info:
        return f"Table {table_name} not found."
    
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    try:
        results = execute_query(query)
        
        # Get column names
        columns = [col['name'] for col in table_info['columns']]
        
        # Format results as text
        output = f"Sample data from {table_name} (showing up to {limit} rows):\n\n"
        output += " | ".join(columns) + "\n"
        output += "-" * (sum(len(col) for col in columns) + 3 * (len(columns) - 1)) + "\n"
        
        for row in results:
            output += " | ".join(str(val) for val in row) + "\n"
        
        return output
    except Exception as e:
        return f"Error retrieving sample data from {table_name}: {str(e)}"

def get_table_row_count(table_name):
    """
    Get the number of rows in a table.
    """
    try:
        results = execute_query(f"SELECT COUNT(*) FROM {table_name}")
        return f"Table {table_name} has {results[0][0]} rows."
    except Exception as e:
        return f"Error counting rows in {table_name}: {str(e)}"

def generate_context_for_llm(query=None, table_names=None):
    """
    Generate context about the database for the LLM based on a user query.
    Optionally focus on specific tables if table_names is provided.
    """
    # Start with schema description
    context = get_db_schema_description()
    
    # If specific tables are mentioned, include sample data for those tables
    if table_names:
        for table_name in table_names:
            context += "\n" + get_table_row_count(table_name) + "\n"
            context += get_table_sample_data(table_name) + "\n"
    
    # Include the user query if provided
    if query:
        context += f"\nUser Query: {query}\n"
    
    return context 