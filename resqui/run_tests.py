import unittest
import xml.etree.ElementTree as ET
import time
import sys


class XMLTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []
        self.start_time = None
        self.test_start_times = {}
        self.test_status = {}

    def startTestRun(self):
        self.start_time = time.time()

    def startTest(self, test):
        """Record the test start time and print test name."""
        self.test_start_times[test] = time.time()
        self.test_status[test] = "success"
        super().startTest(test)

    def stopTest(self, test):
        """Record elapsed time unless already marked as failure/error."""
        duration = time.time() - self.test_start_times.pop(test, time.time())
        if test not in self.test_status or self.test_status[test] == "success":
            self.test_results.append(("success", test, "", duration))
            self.stream.writeln(f"✔ {test} (PASSED)")

    def addFailure(self, test, err):
        """Record test failure and print it."""
        duration = time.time() - self.test_start_times.pop(test, time.time())
        message = self._exc_info_to_string(err, test)
        self.test_status[test] = "failure"
        self.test_results.append(("failure", test, message, duration))
        self.stream.writeln(f"✘ {test} (FAILED)")  # Print failure
        super().addFailure(test, err)

    def addError(self, test, err):
        """Record test error and print it."""
        duration = time.time() - self.test_start_times.pop(test, time.time())
        message = self._exc_info_to_string(err, test)
        self.test_status[test] = "error"
        self.test_results.append(("error", test, message, duration))
        self.stream.writeln(f"⚠ {test} (ERROR)")
        super().addError(test, err)

    def generate_xml_report(self, output_file="test_results.xml"):
        """Generate a JUnit-compatible XML report."""
        root = ET.Element("testsuite")
        root.set("name", "unittest")
        root.set(
            "timestamp",
            time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self.start_time)),
        )
        root.set("tests", str(len(self.test_results)))
        root.set(
            "errors", str(sum(1 for r in self.test_results if r[0] == "error"))
        )
        root.set(
            "failures",
            str(sum(1 for r in self.test_results if r[0] == "failure")),
        )
        root.set("time", f"{time.time() - self.start_time:.3f}")

        for status, test, message, duration in self.test_results:
            case = ET.SubElement(root, "testcase")
            case.set("name", str(test))
            case.set("classname", test.__class__.__name__)
            case.set("time", f"{duration:.3f}")
            if status in {"failure", "error"}:
                failure_element = ET.SubElement(case, status)
                failure_element.text = message

        tree = ET.ElementTree(root)
        tree.write(output_file, encoding="utf-8", xml_declaration=True)


class XMLTestRunner(unittest.TextTestRunner):
    def __init__(self, output_file="test_results.xml", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_file = output_file

    def _makeResult(self):
        return XMLTestResult(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        result = super().run(test)
        result.generate_xml_report(self.output_file)
        if result.failures or result.errors:
            sys.exit(1)
        return result


if __name__ == "__main__":
    test_dir = "tests"
    suite = unittest.TestLoader().discover(test_dir, pattern="test_*.py")

    runner = XMLTestRunner(verbosity=0)
    runner.run(suite)
