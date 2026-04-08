import ast
import operator
import re
import webbrowser
from datetime import datetime


SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.Num):
        return node.n

    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return SAFE_OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
        operand = _eval_node(node.operand)
        return SAFE_OPERATORS[type(node.op)](operand)

    raise ValueError("Unsupported expression")


def safe_calculate(expression: str):
    expression = (expression or "").strip()
    if not expression:
        return None, "No expression provided."

    try:
        parsed = ast.parse(expression, mode="eval")
        result = _eval_node(parsed.body)
        return result, None
    except ZeroDivisionError:
        return None, "Division by zero."
    except Exception as e:
        return None, str(e)


def open_website(url: str):
    target = (url or "").strip()
    if not target:
        return False, "No website provided."

    if not target.startswith(("http://", "https://")):
        target = "https://" + target

    try:
        webbrowser.open(target)
        return True, f"Opened: {target}"
    except Exception as e:
        return False, f"Failed to open website: {e}"


def get_local_time_text():
    now = datetime.now()
    return now.strftime("Local time: %Y-%m-%d %I:%M:%S %p")


def slugify_filename(text: str, fallback: str = "document") -> str:
    text = (text or "").strip()
    if not text:
        return fallback
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text).strip("_")
    return text or fallback