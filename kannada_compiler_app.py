import re
import subprocess
import sys

# === Tokens ===
tokens = [
    ('TYPE', r'poorna|taran|akshara|sutra|samuha'),
    ('LOOP', r'ella'),
    ('ENDLOOP', r'hagiddare'),
    ('KEYWORD', r'helu'),
    ('STRING', r'"[^"]*"'),
    ('CHAR', r"'[a-zA-Z0-9]'"),
    ('FLOAT', r'\d+\.\d+'),
    ('NUMBER', r'\d+'),
    ('IDENTIFIER', r'[a-zA-Z_]\w*'),
    ('ASSIGN', r'='),
    ('PLUS', r'\+'),
    ('MINUS', r'\-'),
    ('MULTIPLY', r'\*'),
    ('DIVIDE', r'\/'),
    ('SEMICOLON', r';'),
    ('LE', r'<='),
    ('LT', r'<'),
    ('GT', r'>'),
    ('GE', r'>='),
    ('ET',r'=='),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('WHITESPACE', r'\s+'),
    
]

def tokenize(code):
    token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in tokens)
    scanner = re.compile(token_regex)
    result = []
    for match in scanner.finditer(code):
        if match.lastgroup != 'WHITESPACE':
            result.append((match.lastgroup, match.group()))
    return result

# === AST Node Classes ===

class VariableDeclaration:
    def __init__(self, dtype, var, value=None, size=None):
        self.dtype = dtype
        self.var = var
        self.value = value
        self.size = size

class AssignmentStatement:
    def __init__(self, var, expression):
        self.var = var
        self.expression = expression

class PrintStatement:
    def __init__(self, var):
        self.var = var

class LoopStatement:
    def __init__(self, loop_var, start, end, body):
        self.loop_var = loop_var
        self.start = start
        self.end = end
        self.body = body


# === Parser ===
def parse(tokens):
    ast = []
    symbol_table = {}
    i = 0
    while i < len(tokens):
        # Parse declarations with type keyword
        if tokens[i][0] == 'TYPE':
            dtype = tokens[i][1]
            var = tokens[i+1][1]
            symbol_table[var] = dtype
            if i+2 < len(tokens) and tokens[i+2][0] == 'LBRACKET':
                size = tokens[i+3][1]
                ast.append(VariableDeclaration(dtype, var, size=size))
                i += 6  # skip tokens: TYPE, var, LBRACKET, size, RBRACKET, SEMICOLON
            elif i+2 < len(tokens) and tokens[i+2][0] == 'ASSIGN':
                val_token = tokens[i+3]
                ast.append(VariableDeclaration(dtype, var, value=val_token[1]))
                i += 5  # TYPE, var, ASSIGN, value, SEMICOLON
            else:
                ast.append(VariableDeclaration(dtype, var))
                i += 3  # TYPE, var, SEMICOLON

        # Parse print statements (helu)
        elif tokens[i][0] == 'KEYWORD' and tokens[i][1] == 'helu':
            ast.append(PrintStatement(tokens[i+1][1]))
            i += 3  # helu, var, SEMICOLON

        # Parse loop statements
        elif tokens[i][0] == 'LOOP':
            # Expect: ella <loop_var> = <start>; <loop_var> <= <end> hagiddare
            loop_var = tokens[i+1][1]
            start = tokens[i+3][1]
            end = tokens[i+7][1]
            i += 8
            loop_body = []
            # Parse statements inside loop until ENDLOOP encountered
            while i < len(tokens) and tokens[i][0] != 'ENDLOOP':
                sub_tokens = []
                while i < len(tokens) and tokens[i][0] != 'SEMICOLON':
                    sub_tokens.append(tokens[i])
                    i += 1
                if i < len(tokens) and tokens[i][0] == 'SEMICOLON':
                    sub_tokens.append(tokens[i])  # include the semicolon
                    i += 1
                # Parse the sub-statement and extend loop body
                sub_ast, _ = parse(sub_tokens)
                loop_body.extend(sub_ast)
            # Skip the ENDLOOP token
            if i < len(tokens) and tokens[i][0] == 'ENDLOOP':
                i += 1
            ast.append(LoopStatement(loop_var, start, end, loop_body))

        # Parse assignment statements (updates without type)
        elif tokens[i][0] == 'IDENTIFIER' and tokens[i+1][0] == 'ASSIGN':
            var = tokens[i][1]
            expr_tokens = []
            j = i+2
            while j < len(tokens) and tokens[j][0] != 'SEMICOLON':
                expr_tokens.append(tokens[j][1])
                j += 1
            expression = " ".join(expr_tokens)
            ast.append(AssignmentStatement(var, expression))
            i = j + 1

        else:
            i += 1
    return ast, symbol_table

# === Code Generator ===
def indent(level): 
    return '    ' * level

def generate_code(ast, symbol_table, indent_level=1, declared=None):
    if declared is None:
        declared = set()

    lines = []
    for node in ast:
        if isinstance(node, VariableDeclaration):
            # If already declared, treat this as an assignment update
            if node.var in declared:
                if node.value:
                    lines.append(f"{indent(indent_level)}{node.var} = {node.value};")
            else:
                declared.add(node.var)
                c_type = {
                    'poorna': 'int',
                    'taran': 'float',
                    'akshara': 'char',
                    'sutra': 'char',
                    'samuha': 'int'
                }.get(node.dtype, 'int')

                if node.size:
                    lines.append(f"{indent(indent_level)}{c_type} {node.var}[{node.size}];")
                elif node.dtype == 'sutra':
                    lines.append(f'{indent(indent_level)}{c_type} {node.var}[] = {node.value};')
                elif node.dtype == 'akshara':
                    lines.append(f"{indent(indent_level)}{c_type} {node.var} = {node.value};")
                elif node.value:
                    lines.append(f"{indent(indent_level)}{c_type} {node.var} = {node.value};")
                else:
                    lines.append(f"{indent(indent_level)}{c_type} {node.var};")

        elif isinstance(node, AssignmentStatement):
            lines.append(f"{indent(indent_level)}{node.var} = {node.expression};")

        elif isinstance(node, PrintStatement):
            var_type = symbol_table.get(node.var, 'poorna')
            fmt = {
                'poorna': "%d",
                'taran': "%f",
                'akshara': "%c",
                'sutra': "%s",
                'samuha': "%d"
            }.get(var_type, "%d")
            # Special handling: if the variable is a string, no quotes needed
            lines.append(f'{indent(indent_level)}printf("{fmt}\\n", {node.var});')

        elif isinstance(node, LoopStatement):
            lines.append(f"{indent(indent_level)}for (int {node.loop_var} = {node.start}; {node.loop_var} <= {node.end}; {node.loop_var}++) {{")
            declared.add(node.loop_var)
            inner = generate_code(node.body, symbol_table, indent_level + 1, declared.copy())
            lines.extend(inner)
            lines.append(f"{indent(indent_level)}}}")


    return lines

#Intermediate
def generate_intermediate_code(ast):
    tac = []
    temp_count = 1

    def new_temp():
        nonlocal temp_count
        temp = f"t{temp_count}"
        temp_count += 1
        return temp

    for node in ast:
        if isinstance(node, VariableDeclaration):
            if node.value:
                tac.append(f"{node.var} = {node.value}")
            else:
                tac.append(f"{node.var} = ?")  # uninitialized
        elif isinstance(node, AssignmentStatement):
            tac.append(f"{node.var} = {node.expression}")
        elif isinstance(node, LoopStatement):
            loop_var = node.loop_var
            start = node.start
            end = node.end
            tac.append(f"{loop_var} = {start}")
            label = f"L{temp_count}"
            temp_count += 1
            tac.append(f"{label}: if {loop_var} > {end} goto END{label}")
            body_code = generate_intermediate_code(node.body)
            tac.extend(body_code)
            tac.append(f"{loop_var} = {loop_var} + 1")
            tac.append(f"goto {label}")
            tac.append(f"END{label}:")
        elif isinstance(node, PrintStatement):
            tac.append(f"print {node.var}")
    return tac
# === Compilation and Execution ===
def compile_and_run(c_code):
    c_source = '\n'.join(["#include <stdio.h>", "int main() {"] + c_code + ["return 0;", "}"])
    with open("output.c", "w") as f:
        f.write(c_source)
    subprocess.run(["gcc", "output.c", "-o", "output"])
    result = subprocess.run(["./output"], capture_output=True, text=True)
    return result.stdout.strip()


# === Main ===
def main(input_file):
    with open(input_file, "r") as f:
        user_input = f.read()

    print("\n=== Step 1: Lexical Analysis ===")
    token_list = tokenize(user_input)
    for t in token_list:
        print(t)

    print("\n=== Step 2: Syntax Analysis (AST) ===")
    ast_tree, symbol_table = parse(token_list)
    for node in ast_tree:
        print(vars(node))

    print("\n=== Step 3: Generated C Code ===")
    c_code = generate_code(ast_tree, symbol_table)
    for line in c_code:
        print(line)

    print("\n=== Step 3.5: Intermediate Code (Three Address Code) ===")
    tac_code = generate_intermediate_code(ast_tree)
    for line in tac_code:
        print(line)

    print("\n=== Step 4: Compilation & Execution ===")
    output = compile_and_run(c_code)
    print("Output of Program:")
    print(output)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kannada_compiler_final.py <input.knd>")
    else:
        main(sys.argv[1])
