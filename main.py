from utils import parse_line

REGISTERS = "abcdefghijklmnopqrstuvwxyz"
VAR_CHARS = "abcdefghijklmnopqrstuvwxyz_"
VARIABLES = {}
CONSTANTS = {}
N_DEFAULT_VARS = 0

def get_var(name, before="", after=""):
    if name in VARIABLES:
        return before + VARIABLES[name] + after
    elif name in CONSTANTS:
        return CONSTANTS[name]
    raise NameError("'" + name + "' does not exist")

def get_args(arg):
    args = []
    word = ""
    quotes = None
    for char in arg:
        if quotes:
            word += char
            if char == quotes:
                if word:
                    args.append(word)
                    word = ""
                quotes = None
        else:
            if char in (" ", '"', "'", "\t"):
                if word:
                    args.append(word)
                    word = ""
                if char in ("'", '"'):
                    word = char
                    quotes = char
            else:
                word += char
    if quotes:
        raise SyntaxError("Unclosed quotes")
    if word:
        args.append(word)
    return args


def expand_expr(expr):
    quotes = None
    word = ""
    escape = False
    expanded_expr = ""

    for char in expr:
        if quotes:
            expanded_expr += char
            if char == quotes:
                quotes = None

        else:
            if char in VAR_CHARS:
                word += char
            else:
                if word:
                    if char == "(":
                        expanded_expr += word
                    else:
                        expanded_expr += get_var(word, "@")
                    word = ""
                if char in "'\"":
                    quotes = char
                if char not in " \t":
                    expanded_expr += char
                continue
    if word:
        expanded_expr += get_var(word, "@")
    return expanded_expr

def expand_macro(arg):
    quotes = None
    word = ""
    escape = False
    expanded_expr = ""

    for char in arg:
        if escape:
            expanded_expr += char
            continue
        elif char == "\\":
            escape = True
            continue
        if quotes:
            if char == quotes:
                quotes = None
                continue
            expanded_expr += char
        else:
            if char in "'\" \t":
                if word:
                    expanded_expr += get_var(word)
                    word = ""
                if char in "'\"":
                    quotes = char
                continue
            if char not in VAR_CHARS:
                raise SyntaxError("Invalid variable character: '{}'".format(char))
            word += char
    if word:
        expanded_expr += get_var(word)
    return expanded_expr



def expand_input(arg):
    quotes = None
    word = ""
    escape = False
    expanded_expr = ""

    for char in arg:
        if quotes:
            if char == quotes:
                quotes = None
                continue
            expanded_expr += char
        else:
            if char in "'\" \t":
                if word:
                    expanded_expr += get_var(word, "^R")
                    word = ""
                if char in "'\"":
                    quotes = char
                continue
            if char not in VAR_CHARS:
                raise SyntaxError("Invalid variable character: '{}'".format(char))
            word += char
    if word:
        expanded_expr += get_var(word, "^R")
    return expanded_expr


class Macro:
    def __init__(self):
        self.start_idx = 0
        self.bar_length = 0
        self.total_length = 0
        self.total_bar_length = 0
        self.extra_length = 0
        self.length = 0
        self.references = []
        self.next_macro = None
        self.content = ""

    def print(self):
        if self.references:
            fmt = []
            for reference in self.references:
                fmt.append(reference.start_idx)
                fmt.append(reference.total_length)
            print(self.content.format(*fmt,), end="")
        else:
            print(self.content, end="")

    def construct(self):
        if self.next_macro:
            self.references.append(self.next_macro)
            self.content += "gg{}|y{}l@0"


def command_dec(var, arg):
    if var:
        return "2G" + get_var(arg, '"', 'p') + "^X0\"" + var + "D"
    else:
        return "2G" + get_var(arg, '"', 'p') + "^X0D"

def command_inc(var, arg):
    if var:
        return "2G" + get_var(arg, '"', 'p') + "^A0\"" + var + "D"
    else:
        return "2G" + get_var(arg, '"', 'p') + "^A0D"

def command_clear(var, arg):
    assert not var and not arg
    return "G5o^[5GdG"

def command_norm(var, arg):
    assert not var
    return expand_macro(arg)

def command_construct(var, arg):
    assert not var
    macro = expand_macro(arg)
    return "2Gi" + macro + "^[0\"zD@z"

def command_print(var, arg):
    if arg is None:
        return "Go^[p"
    else:
        return "Go%s^[" % expand_input(arg)

def command_literal(var, arg):
    if var:
        return "2Gi%s^[0\"%sD" % (expand_input(arg), var)
    else:
        return "2Gi%s^[0D" % expand_input(arg)

def command_goto(var, arg):
    return ""

def command_eval(var, arg):
    if var:
        return "2G\"=%s^Mp0\"%sD" % (expand_expr(arg), var)
    else:
        return "2G\"=%s^Mp0D" % expand_expr(arg)

def command_input(var, arg):
    if not var:
        raise Exception("Input requires variable to assign to")

    string = "Go%s^[" % expand_input(arg)
    string += "2Gi"
    string +=    "2G.0\""+var+"Dgg{}|y{}l@0"
    string += "^[0y$DGA"
    return string

def command_pause(var, arg):
    assert not var
    if arg:
        string =  "Go%s^[" % expand_input(arg)
        string += "2Gi"
        string +=    "gg{}|y{}l@0"
        string += "^[0\"zy$D"
        return string
    else:
        string =  "2Gi"
        string +=    "gg{}|y{}l@0"
        string += "^[0\"zy$D"
        return string

def command_get_char(var, arg):
    line, col = arg.split(" ")
    string = "/\\%" + expand_input(line) + "l\%" + expand_input(col) + "v^M"
    if var:
        string += "\"" + var
    string += "yl"
    return string

def command_get_char_eval(var, arg):
    line, col = get_args(arg)

    if col.startswith('"') and col.endswith('"'):
        col = col[1:-1]

    if line.startswith('"') and line.endswith('"'):
        line = line[1:-1]

    string = "/\\%^R=" + expand_expr(line) + "^Ml\\%^R=" + expand_expr(col) + "^Mv^M"
    if var:
        string += "\"" + var
    string += "yl"
    return string

def command_sub_at_eval(var, arg):
    line, col, char = get_args(arg)
    search = "/\\%^R"

    if line.startswith('"') and line.endswith('"'):
        search += "=" + expand_expr(line[1:-1])
    else:
        search += get_var(line)
    search += "l\\%^R"

    if col.startswith('"') and col.endswith('"'):
        search += "=" + expand_expr(col[1:-1])
    else:
        search += get_var(col)
    search += "v^Ms"

    if char.startswith('"') and char.endswith('"'):
        search += "^R=" + expand_expr(char[1:-1]) + "^M"
    else:
        search += get_var(char)

    search += "^["
    return search

def command_sub_at(var, arg):
    line, col, char = get_args(arg)
    return "/\\%" + expand_input(line) + "l\\%" + expand_input(col) + "v^Ms" + expand_input(char) + "^["

COMMANDS = {
    "print": command_print,
    "goto": command_goto,
    "eval": command_eval,
    "input": command_input,
    "pause": command_pause,
    "clear": command_clear,
    "norm": command_norm,
    "construct": command_construct,
    "get_char": command_get_char,
    "get_char_eval": command_get_char_eval,
    "sub_at": command_sub_at,
    "sub_at_eval": command_sub_at_eval,
    "inc": command_inc,
    "dec": command_dec,
}


class Statement:
    def __init__(self, indent, var, command, arg):
        self.indent    = indent
        self.command   = command
        self.var       = var
        self.arg       = arg
        self.macro     = Macro()

    def __str__(self):
        return self.command + "(" + self.arg + ")"

class ControlStructure:
    def __init__(self):
        self.parent = None
        self.statements = []

    def __len__(self):
        return len(self.statements)

    def __iter__(self):
        return iter(self.statements)

    def visualise(self, indent=0, indent_growth=4):
        print(indent * " " + self.__class__.__name__ + " {")
        for stmt in self.statements:
            if isinstance(stmt, ControlStructure):
                stmt.visualise(indent + indent_growth)
            else:
                print(" " * (indent + indent_growth) + str(stmt))
        print(indent * " " + "}")

    def handle(self, instr_list, idx):
        pass

    def link(self):
        pass

class IndentControlStructure(ControlStructure):
    def __init__(self):
        super().__init__()

    def handle(self, instr_list, idx):
        indent = instr_list[idx].indent
        while idx < len(instr_list):
            if instr_list[idx].indent > indent:
                raise SyntaxError("Unexpected indent")
            if instr_list[idx].indent < indent:
                if not len(self):
                    raise SyntaxError("Empty indent")
                self.macro = self.statements[0].macro
                return idx

            instr = instr_list[idx]
            if instr.command == "if":
                structure = IfControlStructure()
                structure.macro = instr_list[idx].macro
                idx = structure.handle(instr_list, idx)
                self.statements.append(structure)
            elif instr.command == "while":
                structure = WhileControlStructure()
                structure.macro = instr_list[idx].macro
                idx = structure.handle(instr_list, idx)
                self.statements.append(structure)
            elif instr.command in ("elif", "else"):
                raise SyntaxError("Cannot have 'elif' or 'else' without 'if'")
            else:
                self.statements.append(instr)
                idx += 1
        if not len(self):
            raise SyntaxError("Empty indent")
        self.macro = self.statements[0].macro
        return idx

    def link(self, next_macro=None):
        for i, stmt in enumerate(self.statements):
            if isinstance(stmt, ControlStructure):
                if i < len(self.statements) - 1:
                    stmt.link(self.statements[i+1].macro)
                else:
                    stmt.link(next_macro)
            elif stmt.command == "goto":
                stmt.macro.next_macro = marks[stmt.arg]
            elif stmt.command in ("pause", "input"):
                stmt.macro.next_macro = None
                if i == len(self.statements) - 1:
                    stmt.macro.references.append(next_macro)
                else:
                    stmt.macro.references.append(self.statements[i+1].macro)
            elif i == len(self.statements) - 1:
                stmt.macro.next_macro = next_macro
            else:
                stmt.macro.next_macro = self.statements[i+1].macro

    def generate_macros(self):
        macros = []
        for stmt in self.statements:
            if isinstance(stmt, ControlStructure):
                macros += stmt.generate_macros()
            else:
                if stmt.command in COMMANDS:
                    stmt.macro.content = COMMANDS[stmt.command](stmt.var, stmt.arg)
                else:
                    if stmt.command:
                        literal = stmt.command
                        if stmt.arg:
                            literal += " " + stmt.arg
                    elif stmt.arg:
                        literal = stmt.arg
                    stmt.macro.content = command_literal(stmt.var, literal)
                macros.append(stmt.macro)
        return macros

class WhileControlStructure(ControlStructure):
    def __init__(self):
        super().__init__()
        self.condition = None

    def handle(self, instr_list, idx):
        self.condition = instr_list[idx].arg
        indent = instr_list[idx].indent
        idx += 1
        if idx == len(instr_list):
            raise SyntaxError("Unexpected EOF")
        if instr_list[idx].indent <= indent:
            raise SyntaxError("Expected indent")
        structure = IndentControlStructure()
        self.statements.append(structure)
        idx = structure.handle(instr_list, idx)
        return idx

    def link(self, next_macro=None):
        self.next_macro = next_macro
        for i, stmt in enumerate(self.statements):
            stmt.link(next_macro)

    def generate_macros(self):
        content = "@=" + expand_expr(self.condition) + "?'gg{}|y{}l@0':"
        self.macro.references.append(self.statements[0].macro)
        if self.next_macro:
            self.macro.references.append(self.next_macro)
            content += "'gg{}|y{}l@0'"
        else:
            content += "''"
        self.macro.content = content + "^M"
        self.statements[0].statements[-1].macro.next_macro = self.macro
        macros = [self.macro]
        for stmt in self.statements:
            macros += stmt.generate_macros()
        return macros

class IfControlStructure(ControlStructure):
    def __init__(self):
        super().__init__()
        self.conditions = []
        self.has_else = False

    def visualise(self, indent=0, indent_growth=4):
        print(indent * " " + self.__class__.__name__ + " {")
        for i, stmt in enumerate(self.statements):
            if isinstance(stmt, ControlStructure):
                print((indent + indent_growth) * " ", end="")
                if i == len(self.conditions) and self.has_else:
                    print("else:")
                elif i > 0:
                     print("elif (" + self.conditions[i] + "):")
                else:
                     print("if (" + self.conditions[i] + "):")
                stmt.visualise(indent + indent_growth)
            else:
                print(" " * (indent + indent_growth) + str(stmt))
        print(indent * " " + "}")

    def handle(self, instr_list, idx):
        self.conditions.append(instr_list[idx].arg)
        indent = instr_list[idx].indent
        idx += 1
        if idx == len(instr_list):
            raise SyntaxError("Unexpected EOF")
        if instr_list[idx].indent <= indent:
            raise SyntaxError("Expected indent")
        structure = IndentControlStructure()
        self.statements.append(structure)
        idx = structure.handle(instr_list, idx)
        while idx < len(instr_list) \
                and instr_list[idx].indent == indent:
            if instr_list[idx].command == "elif":
                if self.has_else:
                    raise SyntaxError("'elif' cannot exist after 'else'")
                self.conditions.append(instr_list[idx].arg)
            elif instr_list[idx].command == "else":
                if self.has_else:
                    raise SyntaxError("'else' cannot exist after 'else'")
                self.has_else = True
            else:
                break
            idx += 1
            if idx == len(instr_list):
                raise SyntaxError("Unexpected EOF")
            if instr_list[idx].indent <= indent:
                raise SyntaxError("Expected indent")
            structure = IndentControlStructure()
            self.statements.append(structure)
            idx = structure.handle(instr_list, idx)
        return idx

    def link(self, next_macro=None):
        self.next_macro = next_macro
        for i, stmt in enumerate(self.statements):
            stmt.link(next_macro)

    def generate_macros(self):
        content = "@="
        if self.has_else:
            for i, stmt in enumerate(self.statements[:-1]):
                content += expand_expr(self.conditions[i]) + "?'gg{}|y{}l@0':"
                self.macro.references.append(stmt.macro)
            self.macro.references.append(self.statements[-1].macro)
            content += "'gg{}|y{}l@0'"
        else:
            for i, stmt in enumerate(self.statements):
                content += expand_expr(self.conditions[i]) + "?'gg{}|y{}l@0':"
                self.macro.references.append(stmt.macro)
            if self.next_macro:
                self.macro.references.append(self.next_macro)
                content += "'gg{}|y{}l@0'"
            else:
                content += "''"

        self.macro.content = content + "^M"
        macros = [self.macro]
        for stmt in self.statements:
            macros += stmt.generate_macros()
        return macros


if __name__ == "__main__":
    with open("script.vmc", "r") as f:
        script = f.read()

    stmts = []
    marks = {}
    mark = None

    for line in script.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent, var, command, arg = parse_line(line)

        if command == "constant":
            if var in CONSTANTS:
                raise SyntaxError(f"Constant '{var}' already exists")
            CONSTANTS[var] = arg
            continue

        if var:
            if var not in VARIABLES:
                VARIABLES[var] = REGISTERS[
                    len(VARIABLES) - N_DEFAULT_VARS
                ]
            reg = VARIABLES[var]
        else:
            reg = None

        stmt = Statement(indent, reg, command, arg)

        if stmt.command == "mark":
            if mark:
                raise SyntaxError(
                    f"Statement is already marked as '{mark}'"
                )
            mark = stmt.arg
            if mark in marks:
                raise SyntaxError(
                    f"Mark '{mark}' Already exists"
                )
        else:
            if mark:
                marks[mark] = stmt.macro
                mark = None
            stmts.append(stmt)

    structure = IndentControlStructure()
    structure.handle(stmts, 0)
    structure.link()
    macros = structure.generate_macros()
    for i, macro in enumerate(macros):
        if macro.next_macro and (i == len(macros) - 1 or macro.next_macro != macros[i + 1]):
            macro.construct()
        macro.bar_length = len(macro.content.replace("{}", ""))
        macro.length = len(macro.content
                .replace("{}", "")
                .replace("^[", "j")
                .replace("^M", "e")
                .replace("^R", "f")
                .replace("^V", "f")
                .replace("^A", "f")
                .replace("^X", "f")
       )

    for i in range(100):
        idx = 1
        for m_idx, macro in enumerate(macros):
            macro.start_idx = idx

            if macro.references or not macro.next_macro:
                macro.extra_length = 0
                for reference in macro.references:
                    macro.extra_length += \
                        len(str(reference.start_idx)) + \
                        len(str(reference.total_length))
                macro.total_length = macro.length + macro.extra_length
                macro.total_bar_length = macro.bar_length + macro.extra_length
                idx += macro.total_bar_length
            else:
                length = macro.length
                bar_length = macro.length
                for second_macro in macros[m_idx+1:]:
                    if second_macro.references:
                        length += second_macro.total_length
                        bar_length += second_macro.total_bar_length
                        break
                    else:
                        length += second_macro.length
                        bar_length += second_macro.bar_length
                macro.total_length = length
                macro.total_bar_length = bar_length

                idx += macro.bar_length

    for macro in macros:
        macro.print()
    print()
    print()
    print()
    print("To start the program, type: ggy{}l@0".format(macros[0].total_length))


