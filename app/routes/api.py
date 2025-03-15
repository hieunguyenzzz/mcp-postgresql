from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text
from app.models.dynamic import get_table, reflect_db, get_table_info, execute_query, get_all_tables_info

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/tables', methods=['GET'])
def get_tables():
    """Get a list of all tables in the database."""
    try:
        # Refresh the metadata to ensure we have the latest schema
        reflect_db()
        tables_info = get_all_tables_info()
        return jsonify({
            'status': 'success',
            'data': {
                'tables': list(tables_info.keys())
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting tables: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/tables/<string:table_name>', methods=['GET'])
def get_table_details(table_name):
    """Get detailed information about a specific table."""
    try:
        table_info = get_table_info(table_name)
        if not table_info:
            return jsonify({
                'status': 'error',
                'message': f"Table '{table_name}' not found"
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': table_info
        })
    except Exception as e:
        current_app.logger.error(f"Error getting table details: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/tables/<string:table_name>/rows', methods=['GET'])
def get_table_rows(table_name):
    """Get rows from a specific table with optional filtering."""
    try:
        # Verify table exists
        table = get_table(table_name)
        if not table:
            return jsonify({
                'status': 'error',
                'message': f"Table '{table_name}' not found"
            }), 404
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build the query
        query = f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"
        results = execute_query(query, {'limit': limit, 'offset': offset})
        
        # Get column names for the table
        table_info = get_table_info(table_name)
        columns = [col['name'] for col in table_info['columns']]
        
        # Format results as a list of dictionaries
        rows = []
        for result in results:
            row = {}
            for i, col in enumerate(columns):
                row[col] = result[i]
            rows.append(row)
        
        return jsonify({
            'status': 'success',
            'data': {
                'rows': rows,
                'count': len(rows),
                'limit': limit,
                'offset': offset
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting table rows: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/tables/<string:table_name>/rows', methods=['POST'])
def create_row(table_name):
    """Create a new row in a table."""
    try:
        # Verify table exists
        table = get_table(table_name)
        if not table:
            return jsonify({
                'status': 'error',
                'message': f"Table '{table_name}' not found"
            }), 404
        
        # Get the data from request
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': "No data provided"
            }), 400
        
        # Build column and value lists
        columns = []
        values = []
        params = {}
        
        for col, val in data.items():
            columns.append(col)
            values.append(f":{col}")
            params[col] = val
        
        # Build and execute the query
        columns_str = ", ".join(columns)
        values_str = ", ".join(values)
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str}) RETURNING *"
        
        result = execute_query(query, params)
        
        # Get column names for the table
        table_info = get_table_info(table_name)
        column_names = [col['name'] for col in table_info['columns']]
        
        # Format the result
        created_row = {}
        for i, col in enumerate(column_names):
            if i < len(result[0]):
                created_row[col] = result[0][i]
        
        return jsonify({
            'status': 'success',
            'data': {
                'row': created_row
            }
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating row: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/tables/<string:table_name>/rows/<string:row_id>', methods=['PUT'])
def update_row(table_name, row_id):
    """Update a row in a table by ID."""
    try:
        # Verify table exists
        table = get_table(table_name)
        if not table:
            return jsonify({
                'status': 'error',
                'message': f"Table '{table_name}' not found"
            }), 404
        
        # Get the data from request
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': "No data provided"
            }), 400
        
        # Get primary key column
        table_info = get_table_info(table_name)
        primary_keys = table_info['primary_keys']
        
        if not primary_keys:
            return jsonify({
                'status': 'error',
                'message': f"Table '{table_name}' has no primary key"
            }), 400
        
        primary_key = primary_keys[0]  # Use the first primary key
        
        # Build SET clause and parameters
        set_clauses = []
        params = {}
        
        for col, val in data.items():
            set_clauses.append(f"{col} = :{col}")
            params[col] = val
        
        params['id'] = row_id
        
        # Build and execute the query
        set_clause = ", ".join(set_clauses)
        query = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = :id RETURNING *"
        
        result = execute_query(query, params)
        
        if not result:
            return jsonify({
                'status': 'error',
                'message': f"Row with {primary_key}={row_id} not found"
            }), 404
        
        # Get column names for the table
        column_names = [col['name'] for col in table_info['columns']]
        
        # Format the result
        updated_row = {}
        for i, col in enumerate(column_names):
            if i < len(result[0]):
                updated_row[col] = result[0][i]
        
        return jsonify({
            'status': 'success',
            'data': {
                'row': updated_row
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error updating row: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/tables/<string:table_name>/rows/<string:row_id>', methods=['DELETE'])
def delete_row(table_name, row_id):
    """Delete a row from a table by ID."""
    try:
        # Verify table exists
        table = get_table(table_name)
        if not table:
            return jsonify({
                'status': 'error',
                'message': f"Table '{table_name}' not found"
            }), 404
        
        # Get primary key column
        table_info = get_table_info(table_name)
        primary_keys = table_info['primary_keys']
        
        if not primary_keys:
            return jsonify({
                'status': 'error',
                'message': f"Table '{table_name}' has no primary key"
            }), 400
        
        primary_key = primary_keys[0]  # Use the first primary key
        
        # Build and execute the query
        query = f"DELETE FROM {table_name} WHERE {primary_key} = :id RETURNING *"
        result = execute_query(query, {'id': row_id})
        
        if not result:
            return jsonify({
                'status': 'error',
                'message': f"Row with {primary_key}={row_id} not found"
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': f"Row with {primary_key}={row_id} deleted successfully"
        })
    except Exception as e:
        current_app.logger.error(f"Error deleting row: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/execute', methods=['POST'])
def execute_sql():
    """Execute a custom SQL query (with proper authorization)."""
    try:
        # This endpoint should be properly secured in a production environment
        data = request.json
        if not data or 'query' not in data:
            return jsonify({
                'status': 'error',
                'message': "Query not provided"
            }), 400
        
        query = data['query']
        params = data.get('params', {})
        
        # Execute the query
        result = execute_query(query, params)
        
        # For SELECT queries, return the results
        if query.strip().lower().startswith('select'):
            # Convert result rows to list of dictionaries
            rows = [list(row) for row in result]
            return jsonify({
                'status': 'success',
                'data': {
                    'rows': rows,
                    'count': len(rows)
                }
            })
        
        # For other queries, return success
        return jsonify({
            'status': 'success',
            'message': "Query executed successfully",
            'rows_affected': len(result) if result else 0
        })
    except Exception as e:
        current_app.logger.error(f"Error executing SQL: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 