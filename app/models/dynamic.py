from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, inspect, Table
from sqlalchemy.ext.declarative import declarative_base

db = SQLAlchemy()
metadata = MetaData()

def init_db(app):
    """Initialize the database with the app context."""
    db.init_app(app)
    with app.app_context():
        # Reflect the database
        reflect_db()

def reflect_db():
    """Reflect all tables from the database."""
    metadata.reflect(bind=db.engine)
    return metadata

def get_tables():
    """Get all tables from the database."""
    return metadata.tables

def get_table(table_name):
    """Get a specific table from the database."""
    if table_name in metadata.tables:
        return metadata.tables[table_name]
    return None

def get_engine():
    """Get the SQLAlchemy engine."""
    return db.engine

def execute_query(query, params=None):
    """Execute a raw SQL query and return the results."""
    with db.engine.connect() as connection:
        if params:
            result = connection.execute(query, params)
        else:
            result = connection.execute(query)
        return result.fetchall()

def get_table_info(table_name):
    """Get detailed information about a table."""
    if table_name not in metadata.tables:
        return None
    
    table = metadata.tables[table_name]
    inspector = inspect(db.engine)
    
    # Get column information
    columns = []
    for column in inspector.get_columns(table_name):
        columns.append({
            'name': column['name'],
            'type': str(column['type']),
            'nullable': column['nullable'],
            'default': column['default'],
            'primary_key': column.get('primary_key', False)
        })
    
    # Get foreign key information
    foreign_keys = []
    for fk in inspector.get_foreign_keys(table_name):
        foreign_keys.append({
            'constrained_columns': fk['constrained_columns'],
            'referred_table': fk['referred_table'],
            'referred_columns': fk['referred_columns']
        })
    
    # Get primary key information
    primary_keys = inspector.get_pk_constraint(table_name)
    
    return {
        'name': table_name,
        'columns': columns,
        'foreign_keys': foreign_keys,
        'primary_keys': primary_keys['constrained_columns'] if primary_keys else []
    }

def get_all_tables_info():
    """Get detailed information about all tables."""
    table_info = {}
    for table_name in metadata.tables:
        table_info[table_name] = get_table_info(table_name)
    return table_info 