import unittest
import xml.etree.ElementTree as ET
import time


class XMLTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.start_time = None
        self.test_results = []

    def startTestRun(self):
        self.start_time = time.time()

    def addSuccess(self, test):
        self.test_results.append(("success", test, 0))

    def addFailure(self, test, err):
        self.test_results.append(("failure", test, self.prettify(err, test)))

    def addError(self, test, err):
        self.test_results.append(("error", test, self.prettify(err, test)))

    def prettify(self, err, test):
        return self._exc_info_to_string(err, test)

    def generate_xml_report(self, output_file="test_results.xml"):
        r = ET.Element("testsuite")
        results = self.test_results
        r.set("name", "unittest")
        r.set("tests", str(len(results)))
        r.set("errors", str(sum(1 for r in results if r[0] == "error")))
        r.set("failures", str(sum(1 for r in results if r[0] == "failure")))
        r.set("time", f"{time.time() - self.start_time:.3f}")

        for status, test, message in results:
            case = ET.SubElement(r, "testcase")
            case.set("name", str(test))
            case.set("classname", test.__class__.__name__)
            if status in {"failure", "error"}:
                failure_element = ET.SubElement(case, status)
                failure_element.text = message

        tree = ET.ElementTree(r)
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
        return result


# Example Test Case
class ExampleTest(unittest.TestCase):
    def test_success(self):
        self.assertEqual(1 + 1, 2)

    def test_failure(self):
        self.assertEqual(1 + 1, 3)


if __name__ == "__main__":
    runner = XMLTestRunner(verbosity=2)
    unittest.main(testRunner=runner, exit=False)
