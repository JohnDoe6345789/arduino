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
import sys
from dataclasses import dataclass
from pathlib import Path
import re
import textwrap

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
            if issue.level == "ERROR":
                overall_status = 1

    return overall_status


if __name__ == "__main__":
    sys.exit(main())
