#!/usr/bin/env python3
"""
Database MCP Server
Provides tools for executing SQL queries against configured database connections.
Uses usql (universal SQL CLI) to support ALL database types.
Searches upward from cwd for .opencode/plugins/db/config.json
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import csv
import io

def find_config() -> Optional[Path]:
    """
    Search upward from current directory for .opencode/plugins/db/config.json
    Returns the path to config.json if found, None otherwise.
    """
    current = Path.cwd()
    
    # Keep going up until we hit root
    while True:
        config_path = current / ".opencode" / "plugins" / "db" / "config.json"
        if config_path.exists():
            return config_path
        
        # Check if we've hit the root
        parent = current.parent
        if parent == current:
            return None
        current = parent

def load_config() -> Optional[Dict[str, Any]]:
    """Load database configuration from config.json"""
    config_path = find_config()
    if not config_path:
        return None

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load config: {str(e)}"}

def list_connections() -> Dict[str, Any]:
    """List all available database connections."""
    config = load_config()
    
    if not config:
        return {
            "success": False,
            "error": "No database configuration found. Create .opencode/plugins/db/config.json in your project."
        }
    
    if "error" in config:
        return {"success": False, "error": config["error"]}
    
    connections = config.get("connections", {})
    default_conn = config.get("defaultConnection")
    
    result = {
        "success": True,
        "defaultConnection": default_conn,
        "connections": list(connections.keys())
    }
    
    return result

def execute_sql(sql: str, connection_name: Optional[str] = None, fetch_size: int = 100) -> Dict[str, Any]:
    """
    Execute SQL query against specified connection using usql.
    If connection_name is None, uses defaultConnection.
    """
    config = load_config()
    
    if not config:
        return {
            "success": False,
            "error": "No database configuration found."
        }
    
    if "error" in config:
        return {"success": False, "error": config["error"]}
    
    connections = config.get("connections", {})
    
    # Determine which connection to use
    if connection_name:
        if connection_name not in connections:
            return {
                "success": False,
                "error": f"Connection '{connection_name}' not found. Available: {', '.join(connections.keys())}"
            }
        conn_str = connections[connection_name]
        used_connection = connection_name
    else:
        default = config.get("defaultConnection")
        if not default:
            return {
                "success": False,
                "error": "No connection specified and no defaultConnection set in config."
            }
        if default not in connections:
            return {
                "success": False,
                "error": f"Default connection '{default}' not found in connections."
            }
        conn_str = connections[default]
        used_connection = default
    
    # Execute query using usql
    try:
        # usql command with CSV output format
        cmd = [
            "usql",
            "-c", sql,
            "--csv",
            "--no-rc",
            conn_str
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr or "Query execution failed",
                "connection": used_connection
            }
        
        # Parse CSV output
        output = result.stdout.strip()
        
        if not output:
            # No output - probably INSERT/UPDATE/DELETE
            return {
                "success": True,
                "connection": used_connection,
                "message": "Query executed successfully."
            }
        
        # Parse CSV
        csv_reader = csv.reader(io.StringIO(output))
        rows = list(csv_reader)
        
        if len(rows) < 1:
            return {
                "success": True,
                "connection": used_connection,
                "message": "Query executed successfully (no results)."
            }
        
        # First row is headers
        columns = rows[0]
        data_rows = rows[1:]
        
        # Apply fetch_size limit
        if len(data_rows) > fetch_size:
            data_rows = data_rows[:fetch_size]
            truncated = True
        else:
            truncated = False
        
        response = {
            "success": True,
            "connection": used_connection,
            "columns": columns,
            "rows": data_rows,
            "rowCount": len(data_rows)
        }
        
        if truncated:
            response["truncated"] = True
            response["message"] = f"Results limited to {fetch_size} rows"
        
        return response
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Query execution timed out (30s limit)",
            "connection": used_connection
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "usql not found. Install with: nix-shell -p usql"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "connection": used_connection
        }

def get_table_info(table_name: str, connection_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get detailed information about a table.
    Uses database-specific queries via usql.
    """
    config = load_config()
    
    if not config:
        return {"success": False, "error": "No database configuration found."}
    
    if "error" in config:
        return {"success": False, "error": config["error"]}
    
    connections = config.get("connections", {})
    
    # Determine which connection to use
    if connection_name:
        if connection_name not in connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found."}
        conn_str = connections[connection_name]
        used_connection = connection_name
    else:
        default = config.get("defaultConnection")
        if not default or default not in connections:
            return {"success": False, "error": "No connection specified and no valid defaultConnection."}
        conn_str = connections[default]
        used_connection = default
    
    # Detect database type from connection string
    db_type = conn_str.split("://")[0].lower()
    
    # Database-specific queries for table info
    if db_type in ["postgres", "postgresql"]:
        sql = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """
    elif db_type == "mysql":
        sql = f"DESCRIBE {table_name}"
    elif db_type == "sqlite" or db_type.startswith("sqlite"):
        sql = f"PRAGMA table_info({table_name})"
    elif db_type in ["mssql", "sqlserver", "ms"]:
        sql = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """
    else:
        # Generic fallback - try INFORMATION_SCHEMA
        sql = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
        """
    
    result = execute_sql(sql, used_connection, fetch_size=1000)
    
    if not result.get("success"):
        return result
    
    # Format the result
    if "rows" in result:
        return {
            "success": True,
            "connection": used_connection,
            "table": table_name,
            "columns": result["columns"],
            "rows": result["rows"]
        }
    else:
        return result

def get_database_info(connection_name: Optional[str] = None) -> Dict[str, Any]:
    """Get overview of database including list of tables."""
    config = load_config()
    
    if not config:
        return {"success": False, "error": "No database configuration found."}
    
    if "error" in config:
        return {"success": False, "error": config["error"]}
    
    connections = config.get("connections", {})
    
    # Determine which connection to use
    if connection_name:
        if connection_name not in connections:
            return {"success": False, "error": f"Connection '{connection_name}' not found."}
        conn_str = connections[connection_name]
        used_connection = connection_name
    else:
        default = config.get("defaultConnection")
        if not default or default not in connections:
            return {"success": False, "error": "No connection specified and no valid defaultConnection."}
        conn_str = connections[default]
        used_connection = default
    
    # Detect database type
    db_type = conn_str.split("://")[0].lower()
    
    # Database-specific queries for listing tables
    if db_type in ["postgres", "postgresql"]:
        sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
    elif db_type == "mysql":
        sql = "SHOW TABLES"
    elif db_type == "sqlite" or db_type.startswith("sqlite"):
        sql = """
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """
    elif db_type in ["mssql", "sqlserver", "ms"]:
        sql = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """
    else:
        # Generic fallback
        sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_type = 'BASE TABLE'
            ORDER BY table_name
        """
    
    result = execute_sql(sql, used_connection, fetch_size=1000)
    
    if not result.get("success"):
        return result
    
    # Extract table names from result
    if "rows" in result:
        tables = [row[0] for row in result["rows"]]
        return {
            "success": True,
            "connection": used_connection,
            "type": db_type,
            "tables": tables,
            "tableCount": len(tables)
        }
    else:
        return result

# MCP Server implementation
def handle_call_tool(name: str, arguments: dict) -> dict:
    """Handle tool calls from MCP client."""
    
    if name == "db_list":
        return list_connections()
    
    elif name == "db_execute":
        return execute_sql(
            sql=arguments["sql"],
            connection_name=arguments.get("connection"),
            fetch_size=arguments.get("fetch_size", 100)
        )
    
    elif name == "db_table":
        return get_table_info(
            table_name=arguments["table_name"],
            connection_name=arguments.get("connection")
        )
    
    elif name == "db_info":
        return get_database_info(
            connection_name=arguments.get("connection")
        )
    
    else:
        return {"success": False, "error": f"Unknown tool: {name}"}

def main():
    """Main MCP server loop."""
    
    # Read messages from stdin and respond on stdout
    for line in sys.stdin:
        request = None
        try:
            request = json.loads(line)
            
            # Handle different MCP message types
            if request.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "db-mcp-server",
                            "version": "2.0.0"
                        }
                    }
                }
                
            elif request.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "tools": [
                            {
                                "name": "db_list",
                                "description": "List all available database connections from config",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "db_execute",
                                "description": "Execute SQL query against a database connection (supports ALL databases via usql)",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "sql": {
                                            "type": "string",
                                            "description": "SQL query to execute"
                                        },
                                        "connection": {
                                            "type": "string",
                                            "description": "Connection name (optional, uses defaultConnection if not specified)"
                                        },
                                        "fetch_size": {
                                            "type": "integer",
                                            "description": "Maximum number of rows to return (default: 100)"
                                        }
                                    },
                                    "required": ["sql"]
                                }
                            },
                            {
                                "name": "db_table",
                                "description": "Get detailed information about a table (columns, types, etc)",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "table_name": {
                                            "type": "string",
                                            "description": "Name of the table to inspect"
                                        },
                                        "connection": {
                                            "type": "string",
                                            "description": "Connection name (optional, uses defaultConnection if not specified)"
                                        }
                                    },
                                    "required": ["table_name"]
                                }
                            },
                            {
                                "name": "db_info",
                                "description": "Get overview of database including list of all tables",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "connection": {
                                            "type": "string",
                                            "description": "Connection name (optional, uses defaultConnection if not specified)"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
                
            elif request.get("method") == "tools/call":
                tool_name = request["params"]["name"]
                arguments = request["params"].get("arguments", {})
                
                result = handle_call_tool(tool_name, arguments)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {request.get('method')}"
                    }
                }
            
            # Send response
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            req_id = None
            if request is not None:
                req_id = request.get("id")
            error_response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    main()
