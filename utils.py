
var_chars = set("abcdefghijklmnopqrstuvwxyz_")

def parse_line(line):
    idx = 0
    while line[idx] == " ":
        idx += 1
    indent = idx

    var = ""
    while idx < len(line) and line[idx] in var_chars:
        var += line[idx]
        idx += 1

    if idx == len(line):
        assert var
        return indent, None, var, None

    while line[idx] == " ":
        idx += 1

    if line[idx] == "=":
        _, v, command, arg = parse_line(line[idx+1:])
        assert v is None
        return indent, var, command, arg

    return indent, None, var, line[idx:]
