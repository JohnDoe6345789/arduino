#!/usr/bin/env python3
"""
Workflow doctor for GitHub Actions.

This script is designed to help ChatGPT/Codex agents quickly diagnose
common workflow pitfalls without executing the workflows. It validates
that referenced paths exist, highlights unpinned actions, and generally
summarizes potential misconfigurations that frequently cause CI failures.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - dependency guard
    sys.stderr.write(
        "PyYAML is required. Install with `python -m pip install pyyaml`\n"
    )
    sys.exit(1)


@dataclass
class Issue:
    level: str
    message: str
    location: str | None = None
    suggestion: str | None = None

    def format(self) -> str:
        location_prefix = f"[{self.location}] " if self.location else ""
        base = f"{location_prefix}{self.message}"
        if self.suggestion:
            base += f"\n      ↳ {self.suggestion}"
        return base


def ensure_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_workflow(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - parse failures
        raise RuntimeError(f"YAML parsing failed for {path}: {exc}") from exc


def describe_action(action: str) -> str:
    if action.startswith("./") or action.startswith("../"):
        return "local action"
    if action.startswith("docker://"):
        return "docker action"
    return action


def check_action_pins(content: dict, workflow_name: str) -> list[Issue]:
    issues: list[Issue] = []
    for job_id, job in (content.get("jobs") or {}).items():
        for step in job.get("steps", []):
            action = step.get("uses")
            if not isinstance(action, str):
                continue
            if action.startswith(":"):
                # Composite local actions can start with ':'; skip
                continue
            if re.search(r"@[0-9a-f]{40}$", action):
                continue
            if action.startswith("./") or action.startswith("../"):
                continue
            if action.startswith("docker://"):
                continue
            issues.append(
                Issue(
                    level="WARN",
                    location=f"{workflow_name}:{job_id}",
                    message=f"Action `{describe_action(action)}` is not pinned to a commit SHA.",
                    suggestion="Pin actions to full commit SHAs to avoid supply-chain surprises.",
                )
            )
    return issues


def _resolve_workdir(step: dict, job_default: str | None, repo_root: Path) -> Path:
    override = step.get("working-directory")
    target = override or job_default
    return (repo_root / target).resolve() if target else repo_root.resolve()


def _has_cmake_presets(path: Path) -> bool:
    return any((path / candidate).exists() for candidate in ("CMakePresets.json", "CMakeUserPresets.json"))


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _collect_dependency_specs(manifest: dict) -> dict[str, str]:
    deps: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        for name, spec in (manifest.get(key) or {}).items():
            if isinstance(name, str) and isinstance(spec, str):
                deps[name] = spec
    return deps


def _lockfile_specs(lock_data: dict) -> dict[str, str]:
    packages = lock_data.get("packages")
    if isinstance(packages, dict):
        root_manifest = packages.get("")
        if isinstance(root_manifest, dict):
            return _collect_dependency_specs(root_manifest)

    # Fall back to legacy lockfile layout with only resolved versions
    deps: dict[str, str] = {}
    for name, info in (lock_data.get("dependencies") or {}).items():
        if isinstance(name, str) and isinstance(info, dict):
            version = info.get("version")
            if isinstance(version, str):
                deps[name] = version
    return deps


def _npm_ci_mismatches(workdir: Path) -> list[str]:
    package_json = workdir / "package.json"
    lock_candidates = [workdir / "package-lock.json", workdir / "npm-shrinkwrap.json"]
    lock_path = next((candidate for candidate in lock_candidates if candidate.exists()), None)

    errors: list[str] = []
    try:
        package_manifest = _load_json(package_json)
    except FileNotFoundError:
        errors.append("package.json is missing from the npm working directory.")
        return errors
    except json.JSONDecodeError as exc:
        errors.append(f"package.json is not valid JSON: {exc}.")
        return errors

    if lock_path is None:
        errors.append("No package-lock.json or npm-shrinkwrap.json found alongside package.json.")
        return errors

    try:
        lock_data = _load_json(lock_path)
    except json.JSONDecodeError as exc:
        errors.append(f"{lock_path.name} is not valid JSON: {exc}.")
        return errors

    pkg_specs = _collect_dependency_specs(package_manifest)
    lock_specs = _lockfile_specs(lock_data)

    for name, spec in pkg_specs.items():
        locked_spec = lock_specs.get(name)
        if locked_spec is None:
            errors.append(f"{name} is missing from {lock_path.name}.")
        elif locked_spec != spec:
            errors.append(
                f"{name} differs (package.json: {spec!r}, {lock_path.name}: {locked_spec!r})."
            )

    return errors


def check_command_contexts(content: dict, repo_root: Path, workflow_name: str) -> list[Issue]:
    issues: list[Issue] = []
    for job_id, job in (content.get("jobs") or {}).items():
        job_default = ((job.get("defaults") or {}).get("run") or {}).get(
            "working-directory"
        )
        for step in job.get("steps", []):
            run_cmd = step.get("run")
            if not isinstance(run_cmd, str):
                continue

            workdir = _resolve_workdir(step, job_default, repo_root)

            if re.search(r"\b(ctest|cmake)\b[^\n]*--preset", run_cmd):
                if not _has_cmake_presets(workdir):
                    issues.append(
                        Issue(
                            level="ERROR",
                            location=f"{workflow_name}:{job_id}",
                            message="Preset-based CMake/CTest invocation found but no CMakePresets.json nearby.",
                            suggestion="Add CMakePresets.json (or CMakeUserPresets.json) to the working directory or adjust the command.",
                        )
                    )

            if re.search(r"\bconan\s+install\b", run_cmd):
                if not any((workdir / candidate).exists() for candidate in ("conanfile.py", "conanfile.txt")):
                    issues.append(
                        Issue(
                            level="ERROR",
                            location=f"{workflow_name}:{job_id}",
                            message="Conan install invoked without a conanfile in the working directory.",
                            suggestion=f"Ensure conanfile.py or conanfile.txt exists under {workdir} or update the working-directory.",
                        )
                    )

            if re.search(r"pip\s+install\s+conan\b", run_cmd) and "==" not in run_cmd:
                issues.append(
                    Issue(
                        level="WARN",
                        location=f"{workflow_name}:{job_id}",
                        message="Conan is installed without a pinned version; newer releases may change defaults.",
                        suggestion="Pin the Conan version (e.g., `python -m pip install conan==<version>`) to stabilize builds.",
                    )
                )

            if re.search(r"\bnpm\s+ci\b", run_cmd):
                npm_errors = _npm_ci_mismatches(workdir)
                if npm_errors:
                    issues.append(
                        Issue(
                            level="ERROR",
                            location=f"{workflow_name}:{job_id}",
                            message=(
                                "`npm ci` is likely to fail because the lockfile is out of sync with package.json: "
                                + "; ".join(npm_errors)
                            ),
                            suggestion="Regenerate the lockfile with `npm install` or `npm install --package-lock-only` before running CI.",
                        )
                    )

    return issues


def _path_matches(root: Path, pattern: str) -> bool:
    pattern = pattern.lstrip("!")
    # Path.glob understands ** patterns natively.
    return any(root.glob(pattern))


def check_path_filters(content: dict, root: Path, workflow_name: str) -> list[Issue]:
    issues: list[Issue] = []
    events = content.get("on") or {}
    for event_name in ("push", "pull_request"):
        event = events.get(event_name)
        if not isinstance(event, dict):
            continue
        for key in ("paths", "paths-ignore"):
            for pattern in ensure_list(event.get(key)):
                if not isinstance(pattern, str):
                    continue
                if pattern.startswith("!"):
                    # Negations are difficult to evaluate statically; skip
                    continue
                if any(ch in pattern for ch in ("*", "?")):
                    if not _path_matches(root, pattern):
                        issues.append(
                            Issue(
                                level="WARN",
                                location=f"{workflow_name}:{event_name}",
                                message=f"No files in repo match glob `{pattern}` used in `{event_name}.{key}`.",
                                suggestion="Double-check for typos or stale filters that will skip jobs unexpectedly.",
                            )
                        )
                else:
                    candidate = root / pattern
                    if not candidate.exists():
                        issues.append(
                            Issue(
                                level="WARN",
                                location=f"{workflow_name}:{event_name}",
                                message=f"Path `{pattern}` in `{event_name}.{key}` does not exist.",
                                suggestion="Update or remove the filter so pushes/PRs trigger as intended.",
                            )
                        )
    return issues


def check_working_directories(content: dict, root: Path, workflow_name: str) -> list[Issue]:
    issues: list[Issue] = []
    for job_id, job in (content.get("jobs") or {}).items():
        for step in job.get("steps", []):
            wd = step.get("working-directory")
            if not isinstance(wd, str):
                continue
            target = (root / wd).resolve()
            if not target.exists():
                issues.append(
                    Issue(
                        level="ERROR",
                        location=f"{workflow_name}:{job_id}",
                        message=f"Working directory `{wd}` does not exist.",
                        suggestion="Ensure the path is correct or create it before running this step.",
                    )
                )
    return issues


def check_cache_paths(content: dict, root: Path, workflow_name: str) -> list[Issue]:
    issues: list[Issue] = []
    for job_id, job in (content.get("jobs") or {}).items():
        for step in job.get("steps", []):
            settings = step.get("with") or {}
            if not isinstance(settings, dict):
                continue
            cache_paths = ensure_list(settings.get("cache-dependency-path"))
            for cache_path in cache_paths:
                if not isinstance(cache_path, str):
                    continue
                target = root / cache_path
                if not target.exists():
                    issues.append(
                        Issue(
                            level="WARN",
                            location=f"{workflow_name}:{job_id}",
                            message=f"Cache dependency path `{cache_path}` does not exist.",
                            suggestion="Check the file name or generate the dependency file before caching.",
                        )
                    )
    return issues


def inspect_workflow(path: Path, repo_root: Path) -> tuple[str, list[Issue]]:
    content = load_workflow(path)
    workflow_name = content.get("name") or path.name

    issues: list[Issue] = []
    issues.extend(check_action_pins(content, workflow_name))
    issues.extend(check_path_filters(content, repo_root, workflow_name))
    issues.extend(check_working_directories(content, repo_root, workflow_name))
    issues.extend(check_cache_paths(content, repo_root, workflow_name))
    issues.extend(check_command_contexts(content, repo_root, workflow_name))

    return workflow_name, issues


def format_header(title: str, char: str = "=") -> str:
    return f"{title}\n{char * len(title)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose GitHub Actions workflow pitfalls without executing them.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Checks performed:
              - Missing paths in push/pull_request filters
              - Steps that point to non-existent working directories
              - cache-dependency-path entries that are stale
              - Actions that are not pinned to a commit SHA
              - Preset-based cmake/ctest steps lacking CMakePresets.json nearby
              - Conan install steps without a conanfile in the working directory
              - Conan installs performed without pinning the tool version
              - npm ci steps where package.json and the lockfile are out of sync
            """
        ),
    )
    parser.add_argument(
        "--workflows",
        default=Path(".github/workflows"),
        type=Path,
        help="Directory containing workflow YAML files",
    )
    parser.add_argument(
        "--root",
        default=Path("."),
        type=Path,
        help="Repository root used to resolve relative paths",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures to gate CI on diagnostic findings.",
    )
    args = parser.parse_args(argv)

    workflow_dir: Path = args.workflows
    repo_root: Path = args.root

    if not workflow_dir.exists():
        sys.stderr.write(f"Workflow directory {workflow_dir} does not exist.\n")
        return 1

    yaml_files = sorted(
        [p for p in workflow_dir.iterdir() if p.suffix in {".yml", ".yaml"}]
    )

    if not yaml_files:
        sys.stderr.write("No workflow files found.\n")
        return 1

    overall_status = 0
    print(format_header("GitHub Actions workflow diagnosis"))
    for wf in yaml_files:
        try:
            workflow_name, issues = inspect_workflow(wf, repo_root)
        except RuntimeError as exc:
            print(f"\n{wf.name}\n{'-' * len(wf.name)}")
            print(f"  [ERROR] {exc}")
            overall_status = 1
            continue

        print(f"\n{workflow_name}\n{'-' * len(workflow_name)}")
        if not issues:
            print("  No problems detected. ✅")
            continue

        for issue in issues:
            label = "❗" if issue.level == "ERROR" else "⚠️"
            print(f"  {label} {issue.level}: {issue.format()}")
            if issue.level == "ERROR" or (issue.level == "WARN" and args.strict):
                overall_status = 1

    return overall_status


if __name__ == "__main__":
    sys.exit(main())
