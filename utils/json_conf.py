import sys, os, json, re
from datetime import datetime

#========================================
sCommentLinePatt = re.compile("^\s*//.*$")

def readCommentedJSon(fname):
    lines = []
    with open(fname, "r", encoding = "utf-8") as inp:
        for line in inp:
            if not sCommentLinePatt.match(line):
                lines.append(line)
    return "".join(lines)

#========================================
def loadJSonConfig(config_file):
    content = readCommentedJSon(config_file)
    dir_name = os.path.abspath(__file__)
    for idx in range(2):
        dir_name = os.path.dirname(dir_name)
    content = content.replace('${HOME}', dir_name)
    pre_config = json.loads(content)

    file_path_def = pre_config.get("file-path-def")
    if file_path_def:
        for key, value in file_path_def.items():
            assert key != "HOME"
            content = content.replace('${%s}' % key, value)
    return json.loads(content)

#========================================
def _processAlias(content, alias_name, alias_value, aliases_done):
    if not alias_name.isalnum():
        print("Config failure: bad macro name:", repr(alias_name),
            file = sys.stderr)
        assert False
    if alias_name in aliases_done:
        print("Config failure: double use of macro", alias_name,
            file = sys.stderr)
        assert False
    aliases_done.add(alias_name)
    return content.replace('${%s}' % alias_name, alias_value)

#========================================
sSplitInstrPatt = re.compile("^split\('([^']*)'\,\s*'([^\"]*)'\)$")

def _processSpecInstr(instr):
    global sSplitInstrPatt
    q = sSplitInstrPatt.match(instr)
    if q is not None:
        text, separator = q.group(1), q.group(2)
        return text.split(separator)
    assert False

#========================================
def genTS():
    dt = datetime.now()
    return ("%04d-%02d-%02d-%02d-%02d-%02d.%03d" % (dt.year, dt.month,
        dt.day, dt.hour, dt.minute, dt.second, dt.microsecond//1000))

#========================================
sCommentLinePatt = re.compile("^\s*//.*$")

def loadDatasetInventory(inv_file):
    global sCommentLinePatt

    # Check file path correctness
    dir_path = os.path.dirname(inv_file)
    dir_name = os.path.basename(os.path.dirname(inv_file))
    base_name, _, ext = os.path.basename(inv_file).partition('.')
    if dir_name != base_name or ext != "cfg":
        print("Warning: Improper dataset inventory path:",
            inv_file, file = sys.stderr)

    aliases_done = set()
    content = readCommentedJSon(inv_file)
    content = _processAlias(content, "NAME", base_name, aliases_done)
    content = _processAlias(content, "DIR", dir_path, aliases_done)
    content = _processAlias(content, "TS", genTS(), aliases_done)

    pre_config = json.loads(content)

    # Replace predefined names
    for key, value in pre_config.get("aliases", dict()).items():
        if ',' in key:
            try:
                names = key.split(',')
                values = _processSpecInstr(value)
                while len(values) < len(names):
                    values.append("")
                for name, value in zip(names, values):
                    content = _processAlias(content, name, value, aliases_done)
            except Exception:
                print("Config failure: bad special instruction",
                    key, "=", value, file = sys.stderr)
                assert False
        else:
            assert key.isalnum()
            content = _processAlias(key, value, aliases_done)

    # Ready to go
    return json.loads(content)

