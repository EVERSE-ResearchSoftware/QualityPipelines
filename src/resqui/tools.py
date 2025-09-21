import re


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


def indented(text, indent):
    """Indent text by a number of spaces."""
    return "\n".join(" " * indent + line for line in text.splitlines())


def is_commit_hash(ref):
    """
    Returns True if ref looks like a valid git full commit hash.
    """
    return bool(re.fullmatch(r"[0-9a-f]{40}", ref))


def construct_full_url(url, branch_hash_or_tag):
    """
    Construct the full GitHub repository URL for a given branch, (full) hash or tag.
    """
    repo_url = url.rstrip("/")
    if repo_url.endswith(".git"):
        repo_url = url[:-4]
    midfix = "commit" if is_commit_hash(branch_hash_or_tag) else "tree"
    return f"{repo_url}/{midfix}/{branch_hash_or_tag}"


def to_https(url):
    if url.startswith("http://") or url.startswith("https://"):
        return url

    # git@github.com:user/repo.git
    m = re.match(r"git@([^:]+):(.+)", url)
    if m:
        host, path = m.groups()
        return f"https://{host}/{path}"

    # git:// form
    if url.startswith("git://"):
        return "https://" + url[6:]

    return url


def project_name_from_url(url):
    """Infere project name from URL"""
    name = url.rstrip("/").split("/")[-1]
    return name[:-4] if name.endswith(".git") else name
