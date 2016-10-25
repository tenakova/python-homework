class Value:
    def __add__(self, other):
        plus = create_operator('+', lambda lhs, rhs: lhs + rhs)
        return create_expression((self, plus, other))

    def __radd__(self, other):
        return Value.__add__(other, self)

    def __sub__(self, other):
        minus = create_operator('-', lambda lhs, rhs: lhs - rhs)
        return create_expression((self, minus, other))

    def __rsub__(self, other):
        return Value.__sub__(other, self)

    def __mul__(self, other):
        times = create_operator('*', lambda lhs, rhs: lhs * rhs)
        return create_expression((self, times, other))

    def __rmul__(self, other):
        return Value.__mul__(other, self)

    def __truediv__(self, other):
        div = create_operator('/', lambda lhs, rhs: lhs / rhs)
        return create_expression((self, div, other))

    def __rtruediv__(self, other):
        return Value.__truediv__(other, self)

    def __floordiv__(self, other):
        fdiv = create_operator('//', lambda lhs, rhs: lhs // rhs)
        return create_expression((self, fdiv, other))

    def __rfloordiv__(self, other):
        return Value.__floordiv__(other, self)

    def __mod__(self, other):
        mod = create_operator('%', lambda lhs, rhs: lhs % rhs)
        return create_expression((self, mod, other))

    def __rmod__(self, other):
        return Value.__mod__(other, self)

    def __pow__(self, other):
        pw = create_operator('**', lambda lhs, rhs: lhs ** rhs)
        return create_expression((self, pw, other))

    def __rpow__(self, other):
        return Value.__pow__(other, self)

    def __lshift__(self, other):
        lshift = create_operator('<<', lambda lhs, rhs: lhs << rhs)
        return create_expression((self, lshift, other))

    def __rlshift__(self, other):
        return Value.__lshift__(other, self)

    def __rshift__(self, other):
        rshift = create_operator('>>', lambda lhs, rhs: lhs >> rhs)
        return create_expression((self, rshift, other))

    def __rrshift__(self, other):
        return Value.__rshift__(other, self)

    def __and__(self, other):
        and_op = create_operator('&', lambda lhs, rhs: lhs & rhs)
        return create_expression((self, and_op, other))

    def __rand__(self, other):
        return Value.__and__(other, self)

    def __xor__(self, other):
        xor_op = create_operator('^', lambda lhs, rhs: lhs ^ rhs)
        return create_expression((self, xor_op, other))

    def __rxor__(self, other):
        return Value.__xor__(other, self)

    def __or__(self, other):
        or_op = create_operator('|', lambda lhs, rhs: lhs | rhs)
        return create_expression((self, or_op, other))

    def __ror__(self, other):
        return Value.__or__(other, self)


class Constant(Value):
    def __init__(self, value):
        self.value = value

    def evaluate(self, **variables):
        return self.value

    def __str__(self):
        return str(self.value)


class Variable(Value):
    def __init__(self, name):
        self.name = name

    def evaluate(self, **variables):
        return variables[self.name]

    @property
    def get_name(self):
        return self.name

    def __str__(self):
        return str(self.name)


class Operator:
    def __init__(self, symbol, function):
        self.symbol = symbol
        self.function = function

    def call(self, *args):
        return self.function(*args)

    @property
    def get_symbol(self):
        return self.symbol

    def __str__(self):
        return self.symbol


class Expression(Value):
    def __init__(self, expression_structure):
        self.expression_structure = expression_structure

    def evaluate(self, **variables):
        operand1 = self.expression_structure[0]
        operand2 = self.expression_structure[2]
        func = self.expression_structure[1]

        if type(operand1) is tuple or type(operand1) is list:
            operand1 = create_constant(create_expression(operand1).
                                       evaluate(**variables))

        elif isinstance(operand1, (int, float, complex)):
            operand1 = create_constant(operand1)

        if type(operand2) is tuple or type(operand2) is list:
            operand2 = create_constant(create_expression(operand2).
                                       evaluate(**variables))

        elif isinstance(operand2, (int, float, complex)):
            operand2 = create_constant(operand2)

        return func.call(operand1.evaluate(**variables),
                         operand2.evaluate(**variables))

    def __str__(self):
        operand1 = self.expression_structure[0]
        operand2 = self.expression_structure[2]
        func = self.expression_structure[1]

        if type(operand1) is tuple or type(operand1) is list:
            operand1 = str(create_expression(operand1))

        if type(operand2) is tuple or type(operand2) is list:
            operand2 = str(create_expression(operand2))

        return "({} {} {})".format(str(operand1),
                                   func.get_symbol, str(operand2))

    @property
    def variable_names(self):
        names = set()
        operand1 = self.expression_structure[0]
        operand2 = self.expression_structure[2]

        if type(operand1) is tuple or type(operand1) is list:
            operand1 = create_expression(operand1)
            names = names.union(operand1.variable_names)
        elif type(operand1) is Expression:
            names = names.union(operand1.variable_names)
        elif type(operand1) is Variable:
            names = names.union(operand1.get_name)

        if type(operand2) is tuple or type(operand2) is list:
            operand2 = create_expression(operand2)
            names = names.union(operand2.variable_names)
        elif type(operand2) is Expression:
            names = names.union(operand2.variable_names)
        elif type(operand2) is Variable:
            names = names.union(operand2.get_name)

        return names


def create_constant(value):
    return Constant(value)


def create_variable(name):
    return Variable(name)


def create_operator(symbol, function):
    return Operator(symbol, function)


def create_expression(expression_structure):
    return Expression(expression_structure)