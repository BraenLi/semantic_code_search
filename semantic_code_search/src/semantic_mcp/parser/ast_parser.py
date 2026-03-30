"""AST parser for multiple languages using tree-sitter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import tree_sitter_python as tspython
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser as TSParser, Query, QueryCursor


@dataclass
class CodeNode:
    """Represents a parsed code element (function, class, etc.)."""
    node_type: str  # function, class, method, struct
    node_name: str
    code: str
    language: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    ast_path: str = ""
    parent: Optional["CodeNode"] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "node_type": self.node_type,
            "node_name": self.node_name,
            "code": self.code,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_col": self.start_col,
            "end_col": self.end_col,
            "ast_path": self.ast_path,
        }


# Tree-sitter language queries for extracting code elements
QUERY_TEMPLATES = {
    "python": """
    (function_definition) @function
    (class_definition) @class
    """,
    "c": """
    (function_definition) @function
    (struct_specifier) @struct
    """,
    "cpp": """
    (function_definition) @function
    (class_specifier) @class
    (struct_specifier) @struct
    """,
}


class ASTParser:
    """Multi-language AST parser using tree-sitter."""

    def __init__(self, language: str):
        """Initialize parser for given language.

        Args:
            language: One of 'python', 'c', 'cpp'
        """
        self.language_name = language
        self.parser = TSParser()

        # Set language
        if language == "python":
            self.parser.language = Language(tspython.language())
        elif language == "c":
            self.parser.language = Language(tsc.language())
        elif language == "cpp":
            self.parser.language = Language(tscpp.language())
        else:
            raise ValueError(f"Unsupported language: {language}")

        # Load query
        query_source = QUERY_TEMPLATES.get(language, "")
        self.query = Query(self.parser.language, query_source) if query_source else None

    def parse(self, code: str) -> list[CodeNode]:
        """Parse code and extract functions, classes, etc.

        Args:
            code: Source code string

        Returns:
            List of CodeNode objects
        """
        if not self.query:
            return []

        # Parse the code
        tree = self.parser.parse(bytes(code, "utf8"))

        # Execute query using QueryCursor
        cursor = QueryCursor(self.query)
        captures = cursor.captures(tree.root_node)

        nodes = []

        # Process function captures
        if "function" in captures:
            for node in captures["function"]:
                code_node = self._create_code_node(node, "function")
                if code_node:
                    nodes.append(code_node)

        # Process class captures
        if "class" in captures:
            for node in captures["class"]:
                code_node = self._create_code_node(node, "class")
                if code_node:
                    nodes.append(code_node)

        # Process method captures
        if "method" in captures:
            for node in captures["method"]:
                code_node = self._create_code_node(node, "method")
                if code_node:
                    nodes.append(code_node)

        # Process struct captures
        if "struct" in captures:
            for node in captures["struct"]:
                code_node = self._create_code_node(node, "struct")
                if code_node:
                    nodes.append(code_node)

        # Process struct_def captures (for C typedef struct)
        if "struct_def" in captures:
            for node in captures["struct_def"]:
                code_node = self._create_code_node(node, "struct")
                if code_node:
                    nodes.append(code_node)

        # Build parent relationships and AST paths
        self._build_relationships(nodes)

        return nodes

    def _create_code_node(self, node, capture_name: str) -> Optional[CodeNode]:
        """Create CodeNode from tree-sitter node."""
        if capture_name not in ("function", "class", "method", "struct"):
            return None

        # Get node name by recursively searching for identifier
        name_node = self._find_name_node(node)

        if not name_node:
            return None

        code_bytes = node.text
        code_str = code_bytes.decode("utf8") if isinstance(code_bytes, bytes) else code_bytes

        # Get start position
        start_point = node.start_point
        end_point = node.end_point

        return CodeNode(
            node_type=capture_name,
            node_name=name_node.text.decode("utf8") if isinstance(name_node.text, bytes) else name_node.text,
            code=code_str,
            language=self.language_name,
            start_line=start_point[0],
            end_line=end_point[0],
            start_col=start_point[1],
            end_col=end_point[1],
            ast_path=capture_name,
        )

    def _find_name_node(self, node):
        """Recursively find the name identifier node."""
        # For function_definition, look for identifier in function_declarator
        if node.type == "function_definition":
            return self._find_function_name(node)

        # For struct_specifier, look for type_identifier
        if node.type == "struct_specifier":
            return self._find_struct_name(node)

        # Check direct children first
        for child in node.children:
            if child.type in ("identifier", "type_identifier", "field_identifier"):
                return child

        # Recursively search in children
        for child in node.children:
            result = self._find_name_node(child)
            if result:
                return result

        return None

    def _find_struct_name(self, node):
        """Find struct name - may be in type_definition wrapper."""
        # struct_specifier itself doesn't have a name in C
        # The name comes from the type_identifier child if present
        for child in node.children:
            if child.type == "type_identifier":
                return child
        # Return None for anonymous structs
        return None

    def _find_function_name(self, node):
        """Find function name from function_definition node."""
        # Traverse to find the function_declarator then identifier
        for child in node.children:
            if child.type == "pointer_declarator":
                # For pointer returns like: Response* handle_login_request(...)
                return self._find_function_name_in_declarator(child)
            elif child.type == "function_declarator":
                return self._find_function_name_in_declarator(child)
            elif child.type == "identifier":
                return child

        # Fallback to first identifier
        return self._find_name_node(node)

    def _find_function_name_in_declarator(self, node):
        """Find function name from declarator node."""
        for child in node.children:
            if child.type == "function_declarator":
                return self._find_function_name_in_declarator(child)
            elif child.type == "identifier":
                return child
        return None

    def _build_relationships(self, nodes: list[CodeNode]):
        """Build parent relationships and AST paths."""
        # Simple implementation: set AST path based on node type
        for node in nodes:
            if node.node_type == "method":
                # Find parent class
                for other in nodes:
                    if other.node_type == "class" and other.start_line < node.start_line:
                        node.ast_path = f"{other.node_name}/{node.node_type}"
                        node.parent = other
                        break
