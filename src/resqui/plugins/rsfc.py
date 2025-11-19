import json
import subprocess
import tempfile
import os

from resqui.plugins.base import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult

class RSFC(IndicatorPlugin):
    name = "RSFC"
    id = "https://w3id.org/everse/tools/rsfc"
    version = "0.0.4"
    image_url = f"docker.io/amonterodx/rsfc:{version}"
    indicators = [
        "persistent_and_unique_identifier",
        "requirements_specified",
        "has_releases",
        "software_has_citation",
        "software_has_license",
        "software_has_documentation",
        "descriptive_metadata",
        "versioning_standards_use",
        "version_control_use",
        "software_has_tests",
        "repository_workflows",
        "archived_in_software_heritage"
    ]

    def __init__(self, context):
        self.context = context
        self.executor = DockerExecutor(self.image_url)
        self._cache = {}
        
        
    def execute(self, url, commit_hash):
        cache_key = (url, commit_hash)
        if cache_key in self._cache:
            return self._cache[cache_key]

        tempdir = tempfile.mkdtemp()

        url = url[:-4] if url.endswith(".git") else url
        
        run_args = [
            "--rm",
            "-v", f"{tempdir}:/rsfc/outputs",
        ]
        
        _ = self.executor.run([url], run_args=run_args)
        
        files = os.listdir(tempdir)
        if len(files) != 1:
            print("Error: RSFC did not generate any output files")
            raise
        
        report_path = os.path.join(tempdir, files[0])
        with open(report_path) as f:
            report = json.load(f)
            simplified_report = {check["test_id"]: check for check in report["checks"]}
            
        self._cache[cache_key] = simplified_report
        
        return simplified_report
            
        
        
    def persistent_and_unique_identifier(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-01-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-01-1"]["process"],
            status_id=report["RSFC-01-1"]["status"]["@id"],
            output=report["RSFC-01-1"]["output"],
            evidence=report["RSFC-01-1"]["evidence"],
            success=success
        )
    
    
    def software_has_documentation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-05-3"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-05-3"]["process"],
            status_id=report["RSFC-05-3"]["status"]["@id"],
            output=report["RSFC-05-3"]["output"],
            evidence=report["RSFC-05-3"]["evidence"],
            success=success
        )
    
    
    def requirements_specified(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-13-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-13-1"]["process"],
            status_id=report["RSFC-13-1"]["status"]["@id"],
            output=report["RSFC-13-1"]["output"],
            evidence=report["RSFC-13-1"]["evidence"],
            success=success
        )
    
    
    def has_releases(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-03-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-03-1"]["process"],
            status_id=report["RSFC-03-1"]["status"]["@id"],
            output=report["RSFC-03-1"]["output"],
            evidence=report["RSFC-03-1"]["evidence"],
            success=success
        )
    
    
    def software_has_license(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-15-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-15-1"]["process"],
            status_id=report["RSFC-15-1"]["status"]["@id"],
            output=report["RSFC-15-1"]["output"],
            evidence=report["RSFC-15-1"]["evidence"],
            success=success
        )
    
    
    def descriptive_metadata(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-04-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-04-1"]["process"],
            status_id=report["RSFC-04-1"]["status"]["@id"],
            output=report["RSFC-04-1"]["output"],
            evidence=report["RSFC-04-1"]["evidence"],
            success=success
        )
    
    
    def versioning_standards_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-03-3"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-03-3"]["process"],
            status_id=report["RSFC-03-3"]["status"]["@id"],
            output=report["RSFC-03-3"]["output"],
            evidence=report["RSFC-03-3"]["evidence"],
            success=success
        )
    
    
    def version_control_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-17-2"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-17-2"]["process"],
            status_id=report["RSFC-17-2"]["status"]["@id"],
            output=report["RSFC-17-2"]["output"],
            evidence=report["RSFC-17-2"]["evidence"],
            success=success
        )

    
    def software_has_tests(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-14-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-14-1"]["process"],
            status_id=report["RSFC-14-1"]["status"]["@id"],
            output=report["RSFC-14-1"]["output"],
            evidence=report["RSFC-14-1"]["evidence"],
            success=success
        )
    
    
    def software_has_citation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-18-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-18-1"]["process"],
            status_id=report["RSFC-18-1"]["status"]["@id"],
            output=report["RSFC-18-1"]["output"],
            evidence=report["RSFC-18-1"]["evidence"],
            success=success
        )
    
    
    def repository_workflows(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-19-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-19-1"]["process"],
            status_id=report["RSFC-19-1"]["status"]["@id"],
            output=report["RSFC-19-1"]["output"],
            evidence=report["RSFC-19-1"]["evidence"],
            success=success
        )
    
    
    
    def archived_in_software_heritage(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        
        if report["RSFC-08-1"]["output"] == "true":
            success = True
        else:
            success = False
    
        return CheckResult(
            process=report["RSFC-08-1"]["process"],
            status_id=report["RSFC-08-1"]["status"]["@id"],
            output=report["RSFC-08-1"]["output"],
            evidence=report["RSFC-08-1"]["evidence"],
            success=success
        )