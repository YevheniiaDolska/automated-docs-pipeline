#!/usr/bin/env python3
"""
Pipeline Testing Script
Tests all major components of the documentation pipeline
"""

import sys
import subprocess
import shlex
from pathlib import Path
from typing import Tuple, List
import yaml
import json


class PipelineTestRunner:
    """Tests all major flows in the documentation pipeline"""

    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.test_results = []
        self.failed_tests = []

    def run_command(self, command: str, cwd: str = None) -> Tuple[int, str, str]:
        """Execute command and return exit code, stdout, stderr"""
        try:
            cmd_parts = shlex.split(command)
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                cwd=cwd or self.root_dir
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def test_python_scripts_syntax(self) -> bool:
        """Test that all Python scripts have valid syntax"""
        print("\n🔍 Testing Python scripts syntax...")

        python_files = list(Path("scripts").glob("*.py"))
        python_files.extend(Path(".github/workflows").glob("*.py"))

        for py_file in python_files:
            code, _, err = self.run_command(f'python3 -m py_compile "{py_file}"')
            if code != 0:
                self.failed_tests.append(f"Syntax error in {py_file}: {err}")
                return False

        print(f"✅ All {len(python_files)} Python scripts have valid syntax")
        return True

    def test_yaml_files_valid(self) -> bool:
        """Test that all YAML files are valid"""
        print("\n🔍 Testing YAML files...")

        yaml_files = list(self.root_dir.glob("**/*.yml"))
        yaml_files.extend(self.root_dir.glob("**/*.yaml"))

        for yaml_file in yaml_files:
            if ".github" in str(yaml_file) or "node_modules" in str(yaml_file):
                continue

            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
            except Exception as e:
                self.failed_tests.append(f"Invalid YAML in {yaml_file}: {e}")
                return False

        print(f"✅ All {len(yaml_files)} YAML files are valid")
        return True

    def test_frontmatter_validation(self) -> bool:
        """Test frontmatter validation script"""
        print("\n🔍 Testing frontmatter validation...")

        code, out, err = self.run_command("python3 scripts/validate_frontmatter.py")

        if code != 0:
            self.failed_tests.append(f"Frontmatter validation failed: {err}")
            return False

        print("✅ Frontmatter validation working")
        return True

    def test_seo_geo_optimizer(self) -> bool:
        """Test SEO/GEO optimizer"""
        print("\n🔍 Testing SEO/GEO optimizer...")

        # Test basic functionality
        code, out, err = self.run_command("python3 scripts/seo_geo_optimizer.py docs/ --help")

        if code != 0:
            self.failed_tests.append(f"SEO optimizer failed: {err}")
            return False

        # Test actual run
        code, out, err = self.run_command("python3 scripts/seo_geo_optimizer.py docs/")

        if "error" in err.lower() and "no blocking errors" not in out.lower():
            self.failed_tests.append(f"SEO optimizer found errors: {err}")
            return False

        print("✅ SEO/GEO optimizer working")
        return True

    def test_lifecycle_manager(self) -> bool:
        """Test lifecycle manager"""
        print("\n🔍 Testing lifecycle manager...")

        code, out, err = self.run_command("python3 scripts/lifecycle_manager.py --scan")

        if code != 0:
            self.failed_tests.append(f"Lifecycle manager failed: {err}")
            return False

        print("✅ Lifecycle manager working")
        return True

    def test_mkdocs_config(self) -> bool:
        """Test MkDocs configuration"""
        print("\n🔍 Testing MkDocs configuration...")

        # Check if mkdocs.yml exists
        mkdocs_file = self.root_dir / "mkdocs.yml"
        if not mkdocs_file.exists():
            self.failed_tests.append("mkdocs.yml not found")
            return False

        # Validate mkdocs.yml
        try:
            with open(mkdocs_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Check required sections
            required = ['site_name', 'theme', 'plugins', 'nav']
            for req in required:
                if req not in config:
                    self.failed_tests.append(f"Missing required section in mkdocs.yml: {req}")
                    return False

        except Exception as e:
            self.failed_tests.append(f"Invalid mkdocs.yml: {e}")
            return False

        print("✅ MkDocs configuration valid")
        return True

    def test_variables_file(self) -> bool:
        """Test variables file"""
        print("\n🔍 Testing variables file...")

        var_file = self.root_dir / "docs" / "_variables.yml"
        if not var_file.exists():
            self.failed_tests.append("_variables.yml not found")
            return False

        try:
            with open(var_file, 'r', encoding='utf-8') as f:
                variables = yaml.safe_load(f)

            # Check key variables exist
            required_vars = ['product_name', 'default_port', 'cloud_url']
            for var in required_vars:
                if var not in variables:
                    self.failed_tests.append(f"Missing variable: {var}")
                    return False

        except Exception as e:
            self.failed_tests.append(f"Invalid variables file: {e}")
            return False

        print("✅ Variables file valid")
        return True

    def test_code_snippets(self) -> bool:
        """Test VS Code snippets file"""
        print("\n🔍 Testing VS Code snippets...")

        snippets_file = self.root_dir / ".vscode" / "docs.code-snippets"
        if not snippets_file.exists():
            self.failed_tests.append("docs.code-snippets not found")
            return False

        try:
            # VS Code uses JSONC (JSON with Comments), so we need to strip comments
            with open(snippets_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple comment removal for JSONC
            import re
            # Remove single-line comments (but not // inside strings)
            # This is a simplified approach - just remove lines that start with //
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                if not stripped.startswith('//'):
                    cleaned_lines.append(line)
            content = '\n'.join(cleaned_lines)
            # Remove multi-line comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

            snippets = json.loads(content)

            # Check that key snippets exist
            required_snippets = ['Tutorial Document', 'How-To Guide']
            for snippet in required_snippets:
                if snippet not in snippets:
                    self.failed_tests.append(f"Missing snippet: {snippet}")
                    return False

        except Exception as e:
            self.failed_tests.append(f"Invalid snippets file: {e}")
            return False

        print("✅ VS Code snippets valid")
        return True

    def test_github_workflows(self) -> bool:
        """Test GitHub Actions workflows syntax"""
        print("\n🔍 Testing GitHub Actions workflows...")

        workflow_files = list(Path(".github/workflows").glob("*.yml"))

        for workflow in workflow_files:
            try:
                with open(workflow, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Basic validation
                if 'name' not in config:
                    self.failed_tests.append(f"Workflow missing 'name': {workflow}")
                    return False

                # Check for 'on' trigger (YAML may parse it as True)
                if 'on' not in config and True not in config:
                    self.failed_tests.append(f"Workflow missing 'on' trigger: {workflow}")
                    return False

            except Exception as e:
                self.failed_tests.append(f"Invalid workflow {workflow}: {e}")
                return False

        print(f"✅ All {len(workflow_files)} GitHub workflows valid")
        return True

    def test_documentation_files(self) -> bool:
        """Test that documentation files follow standards"""
        print("\n🔍 Testing documentation files...")

        md_files = list(Path("docs").rglob("*.md"))
        issues = []

        for md_file in md_files:
            if md_file.name.startswith("_"):
                continue

            content = md_file.read_text(encoding='utf-8')

            # Check frontmatter exists
            if not content.startswith("---"):
                issues.append(f"{md_file}: Missing frontmatter")
                continue

            # Extract frontmatter
            try:
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = yaml.safe_load(parts[1])

                    # Check required fields
                    if 'title' not in fm:
                        issues.append(f"{md_file}: Missing 'title' in frontmatter")
                    if 'description' not in fm:
                        issues.append(f"{md_file}: Missing 'description' in frontmatter")
                    if 'content_type' not in fm:
                        issues.append(f"{md_file}: Missing 'content_type' in frontmatter")

            except Exception as e:
                issues.append(f"{md_file}: Invalid frontmatter - {e}")

        if issues:
            for issue in issues[:5]:  # Show first 5 issues
                print(f"  ⚠️  {issue}")
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more issues")
            return False

        print(f"✅ All {len(md_files)} documentation files valid")
        return True

    def run_all_tests(self) -> bool:
        """Run all tests and report results"""
        print("="*60)
        print("🚀 DOCUMENTATION PIPELINE TEST SUITE")
        print("="*60)

        tests = [
            ("Python Scripts Syntax", self.test_python_scripts_syntax),
            ("YAML Files", self.test_yaml_files_valid),
            ("Frontmatter Validation", self.test_frontmatter_validation),
            ("SEO/GEO Optimizer", self.test_seo_geo_optimizer),
            ("Lifecycle Manager", self.test_lifecycle_manager),
            ("MkDocs Configuration", self.test_mkdocs_config),
            ("Variables File", self.test_variables_file),
            ("VS Code Snippets", self.test_code_snippets),
            ("GitHub Workflows", self.test_github_workflows),
            ("Documentation Files", self.test_documentation_files),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    self.test_results.append((test_name, "PASSED"))
                else:
                    failed += 1
                    self.test_results.append((test_name, "FAILED"))
            except Exception as e:
                failed += 1
                self.test_results.append((test_name, f"ERROR: {e}"))
                self.failed_tests.append(f"{test_name}: {e}")

        # Print summary
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)

        for test_name, result in self.test_results:
            symbol = "✅" if result == "PASSED" else "❌"
            print(f"{symbol} {test_name}: {result}")

        print("\n" + "-"*60)
        print(f"Total: {passed} passed, {failed} failed")

        if self.failed_tests:
            print("\n❌ FAILED TESTS DETAILS:")
            for failure in self.failed_tests:
                print(f"  - {failure}")

        return failed == 0


def main():
    """Main entry point"""
    tester = PipelineTestRunner()

    if tester.run_all_tests():
        print("\n✅ ALL TESTS PASSED! Pipeline is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
