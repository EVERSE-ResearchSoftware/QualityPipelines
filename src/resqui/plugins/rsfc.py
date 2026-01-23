import json
import tempfile
import os

from resqui.plugins.base import IndicatorPlugin
from resqui.executors import DockerExecutor
from resqui.core import CheckResult

class RSFC(IndicatorPlugin):
    name = "RSFC"
    id = "https://w3id.org/everse/tools/rsfc"
    version = "0.1.0"
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
            "-v", f"{tempdir}:/rsfc/rsfc_output",
        ]
        
        _ = self.executor.run(["--repo", url], run_args=run_args)
        
        files = os.listdir(tempdir)
        if len(files) != 1:
            print("Error: RSFC did not generate any output files")
            raise
        
        report_path = os.path.join(tempdir, files[0])
        with open(report_path) as f:
            report = json.load(f)
            
        self._cache[cache_key] = report
        
        return report
            
        
        
    def persistent_and_unique_identifier(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "persistent_and_unique_identifier" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def software_has_documentation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "software_documentation" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def requirements_specified(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "requirements_specified" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def has_releases(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "has_releases" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def software_has_license(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "software_has_license" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def descriptive_metadata(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "descriptive_metadata" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def versioning_standards_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "versioning_standards_use" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def version_control_use(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "version_control_use" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list

    
    def software_has_tests(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "software_tests" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def software_has_citation(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "software_has_citation" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    def repository_workflows(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "repository_workflows" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
    
    
    
    def archived_in_software_heritage(self, url, branch_hash_or_tag):
        report = self.execute(url, branch_hash_or_tag)
        checks = report["checks"]
        check_list = []
        
        for check in checks:
            if "archived_in_software_heritage" in check["assessesIndicator"]["@id"]:
                if check["output"] == "true":
                    success = True
                else:
                    success = False
                    
                check_res = CheckResult(
                    process=check["process"],
                    status_id=check["status"]["@id"],
                    output=check["output"],
                    evidence=check["evidence"],
                    success=success
                )
                
                check_list.append(check_res)
        
        return check_list
