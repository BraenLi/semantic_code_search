"""Tests for AST parser."""

import pytest
from semantic_mcp.parser.ast_parser import ASTParser, CodeNode


class TestPythonParser:
    """Test Python code parsing."""

    def test_parse_function(self):
        """Should extract function definitions."""
        code = """
def greet(name: str) -> str:
    return f"Hello, {name}!"
"""
        parser = ASTParser("python")
        nodes = parser.parse(code)

        assert len(nodes) == 1
        node = nodes[0]
        assert node.node_type == "function"
        assert node.node_name == "greet"
        assert node.language == "python"
        assert "greet" in node.code
        assert "name: str" in node.code

    def test_parse_class(self):
        """Should extract class definitions with methods."""
        code = """
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def multiply(self, a: int, b: int) -> int:
        return a * b
"""
        parser = ASTParser("python")
        nodes = parser.parse(code)

        # Should find class and methods
        class_nodes = [n for n in nodes if n.node_type == "class"]
        method_nodes = [n for n in nodes if n.node_type == "method"]

        assert len(class_nodes) == 1
        assert class_nodes[0].node_name == "Calculator"
        assert len(method_nodes) == 2

    def test_parse_nested_function(self):
        """Should handle nested functions with correct AST path."""
        code = """
class UserService:
    def authenticate(self, username: str, password: str) -> bool:
        def verify_password(pwd: str) -> bool:
            return pwd == "secret"
        return verify_password(password)
"""
        parser = ASTParser("python")
        nodes = parser.parse(code)

        # Check AST paths are correct - filter for methods only
        auth_methods = [n for n in nodes if n.node_name == "authenticate" and n.node_type == "method"]
        assert len(auth_methods) == 1
        assert "UserService" in auth_methods[0].ast_path


class TestCParser:
    """Test C code parsing."""

    def test_parse_function(self):
        """Should extract C function definitions."""
        code = """
int add(int a, int b) {
    return a + b;
}
"""
        parser = ASTParser("c")
        nodes = parser.parse(code)

        func_nodes = [n for n in nodes if n.node_type == "function"]
        assert len(func_nodes) >= 1
        assert func_nodes[0].node_name == "add"

    def test_parse_struct(self):
        """Should extract C struct definitions."""
        code = """
typedef struct {
    char* name;
    int age;
} Person;
"""
        parser = ASTParser("c")
        nodes = parser.parse(code)

        struct_nodes = [n for n in nodes if n.node_type == "struct"]
        assert len(struct_nodes) >= 1


class TestCppParser:
    """Test C++ code parsing."""

    def test_parse_class(self):
        """Should extract C++ class definitions."""
        code = """
class Rectangle {
private:
    int width;
    int height;
public:
    int area() {
        return width * height;
    }
};
"""
        parser = ASTParser("cpp")
        nodes = parser.parse(code)

        class_nodes = [n for n in nodes if n.node_type == "class"]
        assert len(class_nodes) >= 1
