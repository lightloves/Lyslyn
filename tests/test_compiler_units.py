"""Unit tests for Lyslyn Lexer, Parser, Formatter, and Interpreter."""
import os
import sys
import unittest

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lyslyn.lexer import Lexer
from lyslyn.parser import Parser
from lyslyn.tokens import TokenType
from lyslyn.ast_nodes import (
    SetStmt, IfStmt, WhileStmt, FunctionStmt, ReturnStmt,
    BinaryExpr, VariableExpr, LiteralExpr, HttpStmt
)
from lyslyn.interpreter import Interpreter
from lyslyn.formatter import format_source
from lyslyn.diagnostics import LexerError, ParseError, SemanticError


class TestLexer(unittest.TestCase):
    def test_indentation_and_dedent(self):
        source = "If true:\n    Set x to 1\nSet y to 2\n"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        token_types = [t.type for t in tokens]
        self.assertIn(TokenType.INDENT, token_types)
        self.assertIn(TokenType.DEDENT, token_types)
        self.assertEqual(tokens[-1].type, TokenType.EOF)

    def test_numbers_and_strings(self):
        source = 'Set a to 42\nSet b to 3.14\nSet s to "hello world"\n'
        tokens = Lexer(source).tokenize()
        literals = [t.literal for t in tokens if t.literal is not None]
        self.assertEqual(literals, [42, 3.14, "hello world"])

    def test_unterminated_string_raises_error(self):
        with self.assertRaises(LexerError):
            Lexer('Set s to "unterminated').tokenize()


class TestParser(unittest.TestCase):
    def test_variable_assignment_parse(self):
        source = 'Set username to "Raj"\n'
        p = Parser(Lexer(source).tokenize(), source=source).parse()
        self.assertEqual(len(p.statements), 1)
        stmt = p.statements[0]
        self.assertIsInstance(stmt, SetStmt)
        self.assertEqual(stmt.target.name, "username")
        self.assertEqual(stmt.value.value, "Raj")

    def test_http_request_block_parse(self):
        source = (
            'Send a POST request to "https://api.example.com/items":\n'
            '    headers: {"Content-Type": "application/json"}\n'
            '    data: {"title": "Test"}\n'
            '    timeout: 5\n'
            '    save response as resp\n'
        )
        p = Parser(Lexer(source).tokenize(), source=source).parse()
        self.assertEqual(len(p.statements), 1)
        stmt = p.statements[0]
        self.assertIsInstance(stmt, HttpStmt)
        self.assertEqual(stmt.method, "POST")
        self.assertEqual(stmt.response_var, "resp")


class TestInterpreter(unittest.TestCase):
    def test_arithmetic_and_expressions(self):
        source = "Set result to (10 + 5) * 2 - 4 / 2\n"
        p = Parser(Lexer(source).tokenize(), source=source).parse()
        interp = Interpreter(source=source)
        interp.interpret(p)
        self.assertEqual(interp.environment.get("result"), 28)

    def test_lexical_closure(self):
        source = (
            "Create a function called counter with start:\n"
            "    Set val to start\n"
            "    Create a function called tick:\n"
            "        Increase val by 1\n"
            "        Return val\n"
            "    Return tick\n"
            "Set c to counter(100)\n"
            "Set res1 to c()\n"
            "Set res2 to c()\n"
        )
        p = Parser(Lexer(source).tokenize(), source=source).parse()
        interp = Interpreter(source=source)
        interp.interpret(p)
        self.assertEqual(interp.environment.get("res1"), 101)
        self.assertEqual(interp.environment.get("res2"), 102)


class TestFormatter(unittest.TestCase):
    def test_formatting_indentation_and_casing(self):
        source = "set x to 10\nif x > 5:\nprint x\n"
        formatted = format_source(source)
        self.assertIn("Set x to 10", formatted)
        self.assertIn("    Print x", formatted)


class TestBackendEngine(unittest.TestCase):
    def test_database_crud(self):
        from lyslyn.stdlib.db import DatabaseManager
        mgr = DatabaseManager(":memory:")
        mgr.create_table("items", {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "title": "TEXT", "qty": "INTEGER"})
        inserted = mgr.insert("items", {"title": "Widget", "qty": 10})
        self.assertEqual(inserted["id"], 1)
        found = mgr.find_one("items", {"id": 1})
        self.assertEqual(found["title"], "Widget")
        self.assertEqual(mgr.count("items"), 1)
        mgr.delete("items", {"id": 1})
        self.assertEqual(mgr.count("items"), 0)

    def test_validation_module(self):
        from lyslyn.stdlib.validation import validate_data
        schema = {"name": "required string min:2", "email": "required email"}
        good = validate_data({"name": "Raj", "email": "raj@example.com"}, schema)
        self.assertTrue(good["valid"])
        bad = validate_data({"name": "R", "email": "invalid"}, schema)
        self.assertFalse(bad["valid"])
        self.assertEqual(len(bad["errors"]), 2)


if __name__ == "__main__":
    unittest.main()
