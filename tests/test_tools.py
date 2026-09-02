import unittest
from resqui.tools import (
    is_zenodo_url,
    normalized,
    indented,
    is_commit_hash,
    construct_full_url,
    to_https,
    project_name_from_url,
    ensure_list,
    url_branch_from_full_url,
)

VALID_HASH = "a" * 40
SHORT_HASH = "a" * 39


class TestNormalized(unittest.TestCase):
    def test_removes_leading_indentation(self):
        script = """
            print('hello')
            x = 1
        """
        result = normalized(script)
        self.assertEqual(result, "print('hello')\nx = 1")

    def test_already_clean_script(self):
        script = "print('hello')\nx = 1"
        self.assertEqual(normalized(script), script)

    def test_removes_blank_lines(self):
        script = "\n\n    x = 1\n\n    y = 2\n\n"
        result = normalized(script)
        self.assertNotIn("\n\n", result)


class TestIndented(unittest.TestCase):
    def test_single_line(self):
        self.assertEqual(indented("hello", 4), "    hello")

    def test_multiline(self):
        result = indented("a\nb", 2)
        self.assertEqual(result, "  a\n  b")

    def test_zero_indent(self):
        self.assertEqual(indented("hello", 0), "hello")


class TestIsCommitHash(unittest.TestCase):
    def test_valid_hash(self):
        self.assertTrue(is_commit_hash(VALID_HASH))

    def test_too_short(self):
        self.assertFalse(is_commit_hash(SHORT_HASH))

    def test_too_long(self):
        self.assertFalse(is_commit_hash("a" * 41))

    def test_branch_name(self):
        self.assertFalse(is_commit_hash("main"))

    def test_uppercase_rejected(self):
        self.assertFalse(is_commit_hash("A" * 40))

    def test_mixed_hex(self):
        self.assertTrue(is_commit_hash("0123456789abcdef" * 2 + "01234567"))


class TestConstructFullUrl(unittest.TestCase):
    BASE = "https://github.com/user/repo"

    def test_branch_uses_tree(self):
        url = construct_full_url(self.BASE, "main")
        self.assertIn("/tree/main", url)

    def test_commit_hash_uses_commit(self):
        url = construct_full_url(self.BASE, VALID_HASH)
        self.assertIn("/commit/" + VALID_HASH, url)

    def test_trailing_slash_stripped(self):
        url = construct_full_url(self.BASE + "/", "main")
        self.assertNotIn("//tree", url)

    def test_git_suffix_stripped(self):
        url = construct_full_url(self.BASE + ".git", "main")
        self.assertNotIn(".git", url)


class TestUrlBranchFromFullUrl(unittest.TestCase):
    BASE = "https://github.com/user/repo"

    def test_branch(self):
        url = url_branch_from_full_url(f"{self.BASE}/tree/main")
        self.assertIn("main", url)

    def test_commit_hash(self):
        url = url_branch_from_full_url(f"{self.BASE}/commit/{VALID_HASH}")
        self.assertIn(VALID_HASH, url)


class TestToHttps(unittest.TestCase):
    def test_https_unchanged(self):
        url = "https://github.com/user/repo"
        self.assertEqual(to_https(url), url)

    def test_http_unchanged(self):
        url = "http://github.com/user/repo"
        self.assertEqual(to_https(url), url)

    def test_ssh_converted(self):
        result = to_https("git@github.com:user/repo.git")
        self.assertEqual(result, "https://github.com/user/repo.git")

    def test_git_protocol_converted(self):
        result = to_https("git://github.com/user/repo")
        self.assertEqual(result, "https://github.com/user/repo")


class TestProjectNameFromUrl(unittest.TestCase):
    def test_plain_url(self):
        self.assertEqual(
            project_name_from_url("https://github.com/user/myproject"), "myproject"
        )

    def test_git_suffix_stripped(self):
        self.assertEqual(
            project_name_from_url("https://github.com/user/myproject.git"), "myproject"
        )

    def test_trailing_slash(self):
        self.assertEqual(
            project_name_from_url("https://github.com/user/myproject/"), "myproject"
        )


class TestEnsureList(unittest.TestCase):
    def test_list_is_returned_as_is(self):
        lst = [1, 2, 3]
        self.assertIs(ensure_list(lst), lst)

    def test_scalar_is_wrapped(self):
        self.assertEqual(ensure_list(42), [42])

    def test_string_is_wrapped(self):
        self.assertEqual(ensure_list("hello"), ["hello"])

    def test_none_is_wrapped(self):
        self.assertEqual(ensure_list(None), [None])


class TestIsZenodoUrl(unittest.TestCase):
    def test_doi_url(self):
        self.assertTrue(is_zenodo_url("https://doi.org/10.5281/zenodo.87654321"))

    def test_zenodo_url(self):
        self.assertTrue(is_zenodo_url("https://zenodo.org/records/87654321"))

    def test_other_url(self):
        self.assertFalse(is_zenodo_url("https://example.com/"))
