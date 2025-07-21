def normalized(script):
    """
    Removes extra indentation from a script, caused by triple quotes.
    This does not support mixed tab/spaces.

    Use it for better readability in Python sources, where e.g. a shell
    script or Python script in triple quotes needs to be created and
    passed to a subprocess.
    """
    lines = script.splitlines()
    lines = [line for line in lines if line.strip()]  # remove empty lines
    first_line = lines[0]
    leading_whitespace = len(first_line) - len(first_line.lstrip())
    return "\n".join(line[leading_whitespace:] for line in lines)
