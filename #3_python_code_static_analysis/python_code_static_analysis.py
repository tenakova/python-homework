import re
import ast
from collections import Counter


class Errors:
    def __init__(self):
        self.errors = {}
        self.critic_rules = {
            "line_length": 79,
            "forbid_semicolons": True,
            "max_nesting": None,
            "indentation_size": 4,
            "methods_per_class": None,
            "max_arity": None,
            "forbid_trailing_whitespace": True,
            "max_lines_per_function": None
        }
        self.lines_with_multiple_expressions = {}

    def append_errors(self, new_errors):
        for line, errors in new_errors.items():
            if line in self.errors:
                self.errors[line] += errors
            else:
                self.errors[line] = errors

    def check_line_length(self, code):
        error_message = "line too long ({} > {})"
        max_length = self.critic_rules['line_length']
        line_length_errors = {}
        for line in range(len(code)):
            line_length = len(code[line])
            if line_length > max_length:
                line_length_errors[line + 1] = [
                    error_message.format(line_length, max_length)]

        if line_length_errors:
            self.append_errors(line_length_errors)

    def check_trailing_whitespace(self, code):
        if not self.critic_rules["forbid_trailing_whitespace"]:
            return
        error_message = 'trailing whitespace'
        whitespace_errors = {}
        for line in range(len(code)):
            if re.search(r'\s$', code[line]):
                whitespace_errors[line + 1] = [error_message]

        if whitespace_errors:
            self.append_errors(whitespace_errors)

    def check_methods_per_class(self, tree):
        if self.critic_rules['methods_per_class'] is None:
            return
        error_message = 'too many methods in class({} > {})'
        max_methods = self.critic_rules['methods_per_class']
        methods_per_class_errors = {}
        methods_counter = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.FunctionDef):
                        methods_counter += 1
                if methods_counter > max_methods:
                    methods_per_class_errors[node.lineno] = \
                        [error_message.format(methods_counter, max_methods)]
                methods_counter = 0

        if methods_per_class_errors:
            self.append_errors(methods_per_class_errors)

    def check_number_of_arguments(self, tree):
        if self.critic_rules["max_arity"] is None:
            return

        error_message = "too many arguments({} > {})"
        max_arg = self.critic_rules["max_arity"]
        number_of_arguments_errors = {}

        functions = [f for f in ast.walk(tree) if
                     isinstance(f, ast.FunctionDef)]
        for func in functions:
            args_counter = len(func.args.args) + bool(func.args.vararg) + bool(
                func.args.kwarg)
            if args_counter > max_arg:
                number_of_arguments_errors[func.lineno] = \
                    [error_message.format(args_counter, max_arg)]

        if number_of_arguments_errors:
            self.append_errors(number_of_arguments_errors)

    def check_function_lines(self, tree):
        if not self.critic_rules["max_lines_per_function"]:
            return

        functions = [node for node in ast.walk(tree)
                     if isinstance(node, ast.FunctionDef)]
        error_message = 'method with too many lines ({} > {})'
        lines_per_function_errors = {}

        for func in functions:
            current_level = [func]
            lines = []
            next_level = []
            while current_level:
                for node in current_level:
                    next_level += [n for n in ast.iter_child_nodes(node)
                                   if not isinstance(n, ast.arguments)]
                current_lines = [n.lineno for n in current_level
                                 if hasattr(n, "lineno")]
                lines += current_lines
                current_level = next_level
                next_level = []

            lines_count = len(set(lines))-1
            if self.lines_with_multiple_expressions:
                for line, occurrences in \
                        self.lines_with_multiple_expressions.items():
                    lines_count += \
                        (self.lines_with_multiple_expressions[line]-1)
            if lines_count > self.critic_rules["max_lines_per_function"]:
                lines_per_function_errors[func.lineno] = \
                    [error_message.format(lines_count,
                     self.critic_rules["max_lines_per_function"])]

        if lines_per_function_errors:
            self.append_errors(lines_per_function_errors)

    @staticmethod
    def is_nested(node):
        types = [ast.FunctionDef, ast.ClassDef, ast.If, ast.For, ast.While,
                 ast.FunctionDef, ast.Try, ast.With]
        return type(node) in types

    def check_nesting(self, tree, nesting_counter=0):
        if self.critic_rules["max_nesting"] is None:
            return

        error_message = 'nesting too deep ({} > {})'
        nesting_errors = {}
        if nesting_counter > self.critic_rules["max_nesting"]:
            nesting_errors[(tree.lineno + 1)] = \
                [error_message.format
                 (nesting_counter, self.critic_rules["max_nesting"])]

        if nesting_errors:
            self.append_errors(nesting_errors)

        for node in ast.iter_child_nodes(tree):
            if self.is_nested(node):
                self.check_nesting(node, (nesting_counter + 1))

    @staticmethod
    def is_logical(node):
        types = [ast.Expr, ast.Return, ast.Assign]
        return type(node) in types

    def check_indentation(self, tree, expected_indentation=0):
        error_message = 'indentation is {} instead of {}'
        indentation_errors = {}
        nodes = [node for node in ast.iter_child_nodes(tree)
                 if self.is_nested(node) or self.is_logical(node)]
        checked_lines = set()

        for node in nodes:
            if node.col_offset != expected_indentation \
                    and node.lineno not in checked_lines:
                indentation_errors[node.lineno] = \
                    [error_message.format(node.col_offset,
                                          expected_indentation)]
            if hasattr(node, 'lineno'):
                    checked_lines.add(node.lineno)

        if indentation_errors:
            self.append_errors(indentation_errors)
        for node in ast.iter_child_nodes(tree):
            if self.is_nested(node):
                self.check_indentation(node,
                                       (expected_indentation +
                                        self.critic_rules["indentation_size"]))

    def check_semicolons(self, tree):
        error_message = 'multiple expressions on the same line'
        semicolon_errors = {}
        line_numbers = []

        for node in ast.walk(tree):
            if self.is_logical(node):
                line_numbers.append(node.lineno)

        if len(line_numbers) != len(set(line_numbers)):
            line_occurrences = Counter(line_numbers)
            self.lines_with_multiple_expressions = \
                {line: occurrences for line, occurrences
                 in line_occurrences.items() if occurrences > 1}
            for line, occurrences in \
                    self.lines_with_multiple_expressions.items():
                semicolon_errors[line] = [error_message]
        if semicolon_errors and self.critic_rules["forbid_semicolons"]:
            self.append_errors(semicolon_errors)


def critic(code, **rules):
    result_errors = Errors()
    result_errors.critic_rules.update(rules)
    split_code = code.split(sep="\n")
    tree = ast.parse(code, mode="exec")

    result_errors.check_line_length(split_code)
    result_errors.check_trailing_whitespace(split_code)
    result_errors.check_semicolons(tree)
    result_errors.check_methods_per_class(tree)
    result_errors.check_number_of_arguments(tree)
    result_errors.check_function_lines(tree)
    result_errors.check_nesting(tree)
    result_errors.check_indentation(tree)

    return result_errors.errors
