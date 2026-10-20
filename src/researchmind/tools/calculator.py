"""Safe arithmetic calculator for ResearchMind tools."""

import ast
import math

MAX_EXPRESSION_LENGTH = 200
MAX_AST_NODES = 50
MAX_ABSOLUTE_VALUE = 1e100
MAX_EXPONENT = 100


def calculate(expression: str) -> float:
    """Evaluate a restricted arithmetic expression without eval or exec."""
    expression = expression.strip()

    if not expression:
        raise ValueError("Expression cannot be empty.")

    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("Expression is too long.")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Invalid arithmetic expression.") from exc

    if len(list(ast.walk(tree))) > MAX_AST_NODES:
        raise ValueError("Expression is too complex.")

    try:
        result = _evaluate(tree.body)
    except ZeroDivisionError as exc:
        raise ValueError("Division by zero is not allowed.") from exc
    except OverflowError as exc:
        raise ValueError("Result exceeds the supported numeric range.") from exc

    return _validate_number(result)


def _validate_number(value: float) -> float:
    """Reject non-finite or excessively large numbers."""
    if not math.isfinite(value):
        raise ValueError("Result must be a finite number.")

    if abs(value) > MAX_ABSOLUTE_VALUE:
        raise ValueError("Number exceeds the supported numeric range.")

    return value


def _evaluate(node: ast.AST) -> float:
    """Evaluate only explicitly supported AST nodes."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed.")

        try:
            return _validate_number(float(node.value))
        except OverflowError as exc:
            raise ValueError("Number exceeds the supported numeric range.") from exc

    if isinstance(node, ast.UnaryOp):
        operand = _evaluate(node.operand)

        if isinstance(node.op, ast.UAdd):
            return operand

        if isinstance(node.op, ast.USub):
            return _validate_number(-operand)

        raise ValueError("Unary operator is not allowed.")

    if isinstance(node, ast.BinOp):
        left = _evaluate(node.left)
        right = _evaluate(node.right)

        if isinstance(node.op, ast.Add):
            result = left + right
        elif isinstance(node.op, ast.Sub):
            result = left - right
        elif isinstance(node.op, ast.Mult):
            result = left * right
        elif isinstance(node.op, ast.Div):
            result = left / right
        elif isinstance(node.op, ast.FloorDiv):
            result = left // right
        elif isinstance(node.op, ast.Mod):
            result = left % right
        elif isinstance(node.op, ast.Pow):
            if not right.is_integer() or abs(right) > MAX_EXPONENT:
                raise ValueError("Exponent must be an integer between -100 and 100.")
            result = left ** int(right)
        else:
            raise ValueError("Binary operator is not allowed.")

        return _validate_number(result)

    raise ValueError("Expression contains an unsupported operation.")
