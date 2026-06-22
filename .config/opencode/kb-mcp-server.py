#!/usr/bin/env python3
"""
Knowledge Base MCP Server
Provides tools for managing a knowledge base with SQLite backend.
Supports entries with tags that have version ranges (e.g., "odoo:18+", "odoo:17-19").
"""

import sqlite3
import json
import sys
import re
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# Database path
DB_PATH = Path.home() / ".config" / "opencode" / "kb.db"

# Workspace directory - captured from MCP initialize rootUri, falls back to cwd
WORKSPACE_DIR: Optional[str] = None

def parse_version_range(version_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse version range string into (min_version, max_version).
    
    Uses '..' as range separator for cleaner syntax:
        "18" -> ("18", "18")          # exactly 18
        "18.." -> ("18", None)        # 18 and up
        "..18" -> (None, "18")        # 18 and earlier
        "17..19" -> ("17", "19")      # 17 through 19
        None -> (None, None)          # no version constraint
    
    Also supports legacy '+' syntax:
        "18+" -> ("18", None)         # 18 and up (same as "18..")
    """
    if not version_str:
        return (None, None)
    
    version_str = version_str.strip()
    
    # Check for ".." range separator
    if '..' in version_str:
        parts = version_str.split('..', 1)
        min_ver = parts[0].strip() if parts[0].strip() else None
        max_ver = parts[1].strip() if parts[1].strip() else None
        return (min_ver, max_ver)
    
    # Legacy "18+" format (convert to "18..")
    if version_str.endswith('+'):
        return (version_str[:-1], None)
    
    # Single version "18"
    return (version_str, version_str)

def init_db():
    """Initialize the knowledge base database with schema."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create entries table (no version field anymore)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create tags table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    
    # Create entry_tags junction table with version range support
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entry_tags (
            entry_id INTEGER,
            tag_id INTEGER,
            version_min TEXT,
            version_max TEXT,
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (entry_id, tag_id, version_min, version_max)
        )
    """)

    # Create directories table and junction table for directory-scoped entries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entry_directories (
            entry_id INTEGER,
            directory_id INTEGER,
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (directory_id) REFERENCES directories(id) ON DELETE CASCADE,
            PRIMARY KEY (entry_id, directory_id)
        )
    """)
    
    # Create full-text search virtual table
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
            title, content, content=entries, content_rowid=id
        )
    """)
    
    # Create triggers to keep FTS in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
            DELETE FROM entries_fts WHERE rowid = old.id;
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
            UPDATE entries_fts SET title = new.title, content = new.content WHERE rowid = new.id;
        END
    """)
    
    conn.commit()
    conn.close()

def _set_directories(cursor, entry_id: int, directories: Optional[List[str]]):
    """Replace all directory associations for an entry."""
    cursor.execute("DELETE FROM entry_directories WHERE entry_id = ?", (entry_id,))
    if directories:
        for dir_path in directories:
            dir_path = dir_path.strip()
            if not dir_path:
                continue
            cursor.execute("INSERT OR IGNORE INTO directories (path) VALUES (?)", (dir_path,))
            cursor.execute("SELECT id FROM directories WHERE path = ?", (dir_path,))
            dir_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT OR IGNORE INTO entry_directories (entry_id, directory_id) VALUES (?, ?)",
                (entry_id, dir_id)
            )


def _get_directories(cursor, entry_id: int) -> List[str]:
    """Get directory paths associated with an entry."""
    cursor.execute("""
        SELECT d.path FROM directories d
        JOIN entry_directories ed ON d.id = ed.directory_id
        WHERE ed.entry_id = ?
        ORDER BY d.path
    """, (entry_id,))
    return [row[0] for row in cursor.fetchall()]


def add_entry(title: str, content: str, tags: Optional[List[Dict[str, str]]] = None,
              directories: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Add a new entry to the knowledge base.
    
    tags format: [{"name": "odoo", "version": "18+"}, {"name": "python"}]
    directories format: ["/home/mx/project", "/home/mx/dev"] - entry is scoped to these directories
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Insert entry
        cursor.execute(
            "INSERT INTO entries (title, content) VALUES (?, ?)",
            (title, content)
        )
        entry_id: int = cursor.lastrowid  # type: ignore[assignment]
        
        # Add tags with versions
        if tags:
            for tag_data in tags:
                tag_name = tag_data.get("name", "").strip().lower()
                if not tag_name:
                    continue
                
                version_str = tag_data.get("version")
                version_min, version_max = parse_version_range(version_str)
                
                # Insert or get tag
                cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                tag_id = cursor.fetchone()[0]
                
                # Link tag to entry with version range
                cursor.execute(
                    """INSERT INTO entry_tags (entry_id, tag_id, version_min, version_max) 
                       VALUES (?, ?, ?, ?)""",
                    (entry_id, tag_id, version_min, version_max)
                )

        # Add directories
        _set_directories(cursor, entry_id, directories)

        conn.commit()
        
        return {
            "success": True,
            "entry_id": entry_id,
            "message": f"Entry '{title}' added successfully with ID {entry_id}"
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def update_entry(entry_id: int, title: Optional[str] = None, content: Optional[str] = None,
                 tags: Optional[List[Dict[str, str]]] = None,
                 directories: Optional[List[str]] = None) -> Dict[str, Any]:
    """Update an existing entry. Pass directories=None to leave unchanged, directories=[] to clear all."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check if entry exists
        cursor.execute("SELECT id FROM entries WHERE id = ?", (entry_id,))
        if not cursor.fetchone():
            return {"success": False, "error": f"Entry with ID {entry_id} not found"}
        
        # Build update query dynamically
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(entry_id)
            query = f"UPDATE entries SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
        
        # Update tags if provided
        if tags is not None:
            # Remove existing tags
            cursor.execute("DELETE FROM entry_tags WHERE entry_id = ?", (entry_id,))
            # Add new tags
            for tag_data in tags:
                tag_name = tag_data.get("name", "").strip().lower()
                if not tag_name:
                    continue
                
                version_str = tag_data.get("version")
                version_min, version_max = parse_version_range(version_str)
                
                cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                tag_id = cursor.fetchone()[0]
                cursor.execute(
                    """INSERT INTO entry_tags (entry_id, tag_id, version_min, version_max) 
                       VALUES (?, ?, ?, ?)""",
                    (entry_id, tag_id, version_min, version_max)
                )

        # Update directories if provided
        if directories is not None:
            _set_directories(cursor, entry_id, directories if directories else None)

        conn.commit()
        return {"success": True, "message": f"Entry {entry_id} updated successfully"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def remove_entry(entry_id: int) -> Dict[str, Any]:
    """Remove an entry from the knowledge base."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT title FROM entries WHERE id = ?", (entry_id,))
        result = cursor.fetchone()
        
        if not result:
            return {"success": False, "error": f"Entry with ID {entry_id} not found"}
        
        title = result[0]
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()
        
        return {"success": True, "message": f"Entry '{title}' (ID {entry_id}) removed successfully"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def format_tag_with_version(tag_name: str, version_min: Optional[str], version_max: Optional[str]) -> str:
    """Format a tag with its version range for display using '..' syntax."""
    if version_min is None and version_max is None:
        return tag_name
    elif version_min is None:
        return f"{tag_name}:..{version_max}"
    elif version_max is None:
        return f"{tag_name}:{version_min}.."
    elif version_min == version_max:
        return f"{tag_name}:{version_min}"
    else:
        return f"{tag_name}:{version_min}..{version_max}"

def search_entries(query: Optional[str] = None, tags: Optional[List[Dict[str, str]]] = None,
                   directory: Optional[str] = None,
                   read: bool = False) -> Dict[str, Any]:
    """
    Search entries by text query and/or tags with version ranges.
    
    tags format: [{"name": "odoo", "version": "18"}] - finds entries tagged with odoo:18, odoo:18+, odoo:17-19, etc.
    
    Directory filtering: if directory is provided (or defaults to WORKSPACE_DIR/cwd), only returns
    entries that are either global (no directories) or scoped to the directory or any ancestor.
    Pass directory="" to skip directory filtering entirely.

    If read=True, returns full content for each entry instead of just snippets.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Resolve directory filter
    if directory is None:
        directory = WORKSPACE_DIR or os.getcwd()
    if directory:
        directory = directory.rstrip('/')

    try:
        # Start building the query
        if query:
            # Use full-text search - escape special chars per FTS5 spec
            # Escape double quotes by doubling them, then wrap in quotes
            escaped = query.replace('"', '""')
            fts_query = f'"{escaped}"'
            base_query = """
                SELECT DISTINCT e.id, e.title, e.created_at, e.updated_at
                FROM entries e
                WHERE e.id IN (SELECT rowid FROM entries_fts WHERE entries_fts MATCH ?)
            """
            params = [fts_query]
        else:
            base_query = """
                SELECT DISTINCT e.id, e.title, e.created_at, e.updated_at
                FROM entries e
                WHERE 1=1
            """
            params = []
        
        # Add tag filters with version matching
        if tags:
            for tag_filter in tags:
                tag_name = tag_filter.get("name", "").strip().lower()
                if not tag_name:
                    continue
                
                version = tag_filter.get("version")
                
                if version:
                    base_query += """
                        AND e.id IN (
                            SELECT et.entry_id
                            FROM entry_tags et
                            JOIN tags t ON et.tag_id = t.id
                            WHERE t.name = ?
                            AND (
                                (et.version_min IS NULL AND et.version_max IS NULL)
                                OR (et.version_min IS NOT NULL AND et.version_max IS NULL AND ? >= et.version_min)
                                OR (et.version_min IS NULL AND et.version_max IS NOT NULL AND ? <= et.version_max)
                                OR (et.version_min IS NOT NULL AND et.version_max IS NOT NULL AND ? >= et.version_min AND ? <= et.version_max)
                            )
                        )
                    """
                    params.extend([tag_name, version, version, version, version])
                else:
                    base_query += """
                        AND e.id IN (
                            SELECT et.entry_id
                            FROM entry_tags et
                            JOIN tags t ON et.tag_id = t.id
                            WHERE t.name = ?
                        )
                    """
                    params.append(tag_name)

        # Add directory filter
        if directory:
            base_query += """
                AND (
                    NOT EXISTS (SELECT 1 FROM entry_directories WHERE entry_id = e.id)
                    OR EXISTS (
                        SELECT 1 FROM entry_directories ed
                        JOIN directories d ON ed.directory_id = d.id
                        WHERE ed.entry_id = e.id
                        AND (d.path = ? OR d.path LIKE ? || '/%' OR ? LIKE d.path || '/%')
                    )
                )
            """
            params.extend([directory, directory, directory])

        base_query += " ORDER BY e.updated_at DESC"
        
        cursor.execute(base_query, params)
        
        results = []
        for row in cursor.fetchall():
            entry_id = row["id"]
            
            # Get all tags with versions for this entry
            cursor.execute("""
                SELECT t.name, et.version_min, et.version_max
                FROM entry_tags et
                JOIN tags t ON et.tag_id = t.id
                WHERE et.entry_id = ?
                ORDER BY t.name
            """, (entry_id,))
            
            tag_list = []
            for tag_row in cursor.fetchall():
                tag_str = format_tag_with_version(
                    tag_row[0], tag_row[1], tag_row[2]
                )
                tag_list.append(tag_str)

            # Get directories for this entry
            dir_list = _get_directories(cursor, entry_id)

            entry = {
                "id": row["id"],
                "title": row["title"],
                "tags": tag_list,
                "directories": dir_list,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            
            if read:
                # Fetch full content
                cursor.execute("SELECT content FROM entries WHERE id = ?", (entry_id,))
                content_row = cursor.fetchone()
                if content_row:
                    entry["content"] = content_row[0]
            elif query:
                # Add snippets for text search
                cursor.execute("""
                    SELECT snippet(entries_fts, 0, '<mark>', '</mark>', '...', 32) as title_snippet,
                           snippet(entries_fts, 1, '<mark>', '</mark>', '...', 64) as content_snippet
                    FROM entries_fts WHERE rowid = ?
                """, (entry_id,))
                snippet_row = cursor.fetchone()
                if snippet_row:
                    entry["title_snippet"] = snippet_row[0]
                    entry["content_snippet"] = snippet_row[1]
            
            results.append(entry)
        
        return {
            "success": True,
            "count": len(results),
            "directory_context": directory or None,
            "entries": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def get_entry(entry_id: int) -> Dict[str, Any]:
    """Get a specific entry by ID with full content."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, title, content, created_at, updated_at
            FROM entries
            WHERE id = ?
        """, (entry_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return {"success": False, "error": f"Entry with ID {entry_id} not found"}
        
        # Get all tags with versions
        cursor.execute("""
            SELECT t.name, et.version_min, et.version_max
            FROM entry_tags et
            JOIN tags t ON et.tag_id = t.id
            WHERE et.entry_id = ?
            ORDER BY t.name
        """, (entry_id,))
        
        tag_list = []
        for tag_row in cursor.fetchall():
            tag_str = format_tag_with_version(
                tag_row[0], tag_row[1], tag_row[2]
            )
            tag_list.append(tag_str)

        # Get directories
        dir_list = _get_directories(cursor, entry_id)

        entry = {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "tags": tag_list,
            "directories": dir_list,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        
        return {"success": True, "entry": entry}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def list_tags() -> Dict[str, Any]:
    """List all unique tags (without versions) in the knowledge base."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT t.name, COUNT(DISTINCT et.entry_id) as count
            FROM tags t
            LEFT JOIN entry_tags et ON t.id = et.tag_id
            GROUP BY t.name
            ORDER BY count DESC, t.name
        """)
        
        tags = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        return {"success": True, "tags": tags}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def list_tag_versions(tag_name: Optional[str] = None) -> Dict[str, Any]:
    """List all tag:version combinations, optionally filtered by tag name."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        if tag_name:
            cursor.execute("""
                SELECT t.name, et.version_min, et.version_max, 
                       COUNT(DISTINCT et.entry_id) as count
                FROM entry_tags et
                JOIN tags t ON et.tag_id = t.id
                WHERE t.name = ?
                GROUP BY t.name, et.version_min, et.version_max
                ORDER BY t.name, et.version_min
            """, (tag_name.lower(),))
        else:
            cursor.execute("""
                SELECT t.name, et.version_min, et.version_max, 
                       COUNT(DISTINCT et.entry_id) as count
                FROM entry_tags et
                JOIN tags t ON et.tag_id = t.id
                GROUP BY t.name, et.version_min, et.version_max
                ORDER BY t.name, et.version_min
            """)
        
        versions = []
        for row in cursor.fetchall():
            tag_str = format_tag_with_version(row[0], row[1], row[2])
            versions.append({"tag": tag_str, "count": row[3]})
        
        return {"success": True, "versions": versions}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def list_directories() -> Dict[str, Any]:
    """List all unique directory paths with entry counts."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT d.path, COUNT(DISTINCT ed.entry_id) as count
            FROM directories d
            LEFT JOIN entry_directories ed ON d.id = ed.directory_id
            GROUP BY d.path
            ORDER BY count DESC, d.path
        """)

        dirs = [{"path": row[0], "count": row[1]} for row in cursor.fetchall()]

        return {"success": True, "directories": dirs}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

# MCP Server implementation
def handle_call_tool(name: str, arguments: dict) -> dict:
    """Handle tool calls from MCP client."""
    
    if name == "kb_add":
        return add_entry(
            title=arguments["title"],
            content=arguments["content"],
            tags=arguments.get("tags"),
            directories=arguments.get("directories")
        )
    
    elif name == "kb_update":
        return update_entry(
            entry_id=arguments["entry_id"],
            title=arguments.get("title"),
            content=arguments.get("content"),
            tags=arguments.get("tags"),
            directories=arguments.get("directories")
        )
    
    elif name == "kb_remove":
        return remove_entry(entry_id=arguments["entry_id"])
    
    elif name == "kb_search":
        return search_entries(
            query=arguments.get("query"),
            tags=arguments.get("tags"),
            directory=arguments.get("directory"),
            read=arguments.get("read", False)
        )
    
    elif name == "kb_get":
        return get_entry(entry_id=arguments["entry_id"])
    
    elif name == "kb_list_tags":
        return list_tags()
    
    elif name == "kb_list_tag_versions":
        return list_tag_versions(tag_name=arguments.get("tag_name"))

    elif name == "kb_list_directories":
        return list_directories()
    
    else:
        return {"success": False, "error": f"Unknown tool: {name}"}

def main():
    """Main MCP server loop."""
    # Initialize database
    init_db()
    
    # Read messages from stdin and respond on stdout
    for line in sys.stdin:
        request = None
        try:
            request = json.loads(line)
            
            # Handle different MCP message types
            if request.get("method") == "initialize":
                # Capture workspace directory from rootUri
                global WORKSPACE_DIR
                root_uri = request.get("params", {}).get("rootUri")
                if root_uri:
                    from urllib.parse import urlparse, unquote
                    parsed = urlparse(root_uri)
                    WORKSPACE_DIR = unquote(parsed.path).rstrip('/')
                else:
                    root_path = request.get("params", {}).get("rootPath")
                    if root_path:
                        WORKSPACE_DIR = root_path.rstrip('/')

                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "kb-mcp-server",
                            "version": "3.0.0"
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
                                "name": "kb_add",
                                "description": "Add a new entry to the knowledge base with tags that can have version ranges and optional directory scoping",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "description": "Entry title"},
                                        "content": {"type": "string", "description": "Entry content"},
                                        "tags": {
                                            "type": "array",
                                            "description": "Tags with optional version ranges",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string", "description": "Tag name"},
                                                    "version": {"type": "string", "description": "Version range: '18' (exact), '18..' (and up), '..18' (up to), '17..19' (range) (optional)"}
                                                },
                                                "required": ["name"]
                                            }
                                        },
                                        "directories": {
                                            "type": "array",
                                            "description": "Directories this entry is scoped to (empty = global, always visible). Ancestor matching: entry for '/home/mx/project' also matches '/home/mx/project/src'",
                                            "items": {"type": "string"}
                                        }
                                    },
                                    "required": ["title", "content"]
                                }
                            },
                            {
                                "name": "kb_update",
                                "description": "Update an existing entry in the knowledge base",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "entry_id": {"type": "integer", "description": "ID of the entry to update"},
                                        "title": {"type": "string", "description": "New title (optional)"},
                                        "content": {"type": "string", "description": "New content (optional)"},
                                        "tags": {
                                            "type": "array",
                                            "description": "New tags with version ranges (replaces all existing tags)",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string", "description": "Tag name"},
                                                    "version": {"type": "string", "description": "Version range: '18' (exact), '18..' (and up), '..18' (up to), '17..19' (range) (optional)"}
                                                },
                                                "required": ["name"]
                                            }
                                        },
                                        "directories": {
                                            "type": "array",
                                            "description": "New directories (replaces all existing). Pass [] to clear and make global. Omit to leave unchanged.",
                                            "items": {"type": "string"}
                                        }
                                    },
                                    "required": ["entry_id"]
                                }
                            },
                            {
                                "name": "kb_remove",
                                "description": "Remove an entry from the knowledge base",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "entry_id": {"type": "integer", "description": "ID of the entry to remove"}
                                    },
                                    "required": ["entry_id"]
                                }
                            },
                            {
                                "name": "kb_search",
                                "description": "Search entries by text query and/or tags with version matching. Automatically filters by current directory context: global entries (no directories) always appear; directory-scoped entries appear if the current directory is the entry's directory or a descendant.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string", "description": "Full-text search query (optional)"},
                                        "tags": {
                                            "type": "array",
                                            "description": "Filter by tags with optional version (optional)",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string", "description": "Tag name"},
                                                    "version": {"type": "string", "description": "Specific version to match (e.g., '18')"}
                                                },
                                                "required": ["name"]
                                            }
                                        },
                                        "directory": {"type": "string", "description": "Override directory context (defaults to MCP workspace root). Pass empty string to disable directory filtering."},
                                        "read": {"type": "boolean", "description": "If true, returns full content for each entry instead of just metadata (default: false)"}
                                    }
                                }
                            },
                            {
                                "name": "kb_get",
                                "description": "Get a specific entry by ID with full content",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "entry_id": {"type": "integer", "description": "ID of the entry to retrieve"}
                                    },
                                    "required": ["entry_id"]
                                }
                            },
                            {
                                "name": "kb_list_tags",
                                "description": "List all unique tag names (without versions) with entry counts",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "kb_list_tag_versions",
                                "description": "List all tag:version combinations with entry counts, optionally filtered by tag name",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "tag_name": {"type": "string", "description": "Filter by specific tag name (optional)"}
                                    }
                                }
                            },
                            {
                                "name": "kb_list_directories",
                                "description": "List all unique directory paths with entry counts",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
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
