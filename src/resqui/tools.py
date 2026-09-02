import re

import requests


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


def url_branch_from_full_url(full_url):
    # https://github.com/user/repo/tree/v1.2.3
    m = re.match(r"(https://github.com/[^/]+/[^/]+)/(commit|tree)/(.+)", full_url)
    if m:
        url, _, branch_hash_or_tag = m.groups()
        return [url, branch_hash_or_tag]


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


def ensure_list(item):
    """Wraps the item into a list if it is not already a list"""
    return item if isinstance(item, list) else [item]


def is_zenodo_url(url):
    return url.startswith("https://doi.org/10.5281/zenodo.") or url.startswith(
        "https://zenodo.org/records/"
    )


def zenodo_url_to_git(url):
    headers = {
        "User-Agent": "EVERSE resqui (+https://everse.software/QualityPipelines/)"
    }

    # Parsing FAIR Signposting headers to find the URL of the REST API endpoint.
    r = requests.get(url, headers=headers)
    links = r.headers.get("Link", "").split(",")
    for link in links:
        [uri, *parameters] = link.split(";")

        parameters_dict = {}
        for parameter in parameters:
            [key, value] = parameter.split("=")
            parameters_dict[key.strip()] = value.strip()

        if (
            parameters_dict.get("rel") == '"describedby"'
            and parameters_dict.get("type") == '"application/json"'
        ):
            # The URI is enclosed in angled brackets.
            rest_uri = uri.strip()[1:-1]

            # Extracting the Git URL from the REST API endpoint.
            r = requests.get(
                rest_uri, headers={**headers, "Accept": "application/json"}
            )
            for related_identifier in r.json()["metadata"].get(
                "related_identifiers", {}
            ):
                if "://github.com/" in related_identifier["identifier"]:
                    full_url = related_identifier["identifier"]
                    url, branch = url_branch_from_full_url(full_url)
                    return [url, branch]

    raise ValueError("No Git repository found for Zenodo URL")
