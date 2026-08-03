"""Behavior tests for the public architecture-research Skill helper."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / ".agents"
    / "skills"
    / "open-source-architecture-research"
    / "scripts"
    / "research_architecture.py"
)


def load_research_module() -> object:
    spec = importlib.util.spec_from_file_location("architecture_research", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("architecture research helper is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OpenSourceArchitectureResearchTests(unittest.TestCase):
    def test_inspect_project_extracts_architecture_signals(self) -> None:
        research = load_research_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Indoor robot\nROS 2 navigation, localization, and safety gate.\n",
                encoding="utf-8",
            )
            (root / "docs" / "architecture").mkdir(parents=True)
            (root / "docs" / "architecture" / "system.md").write_text(
                "Simulation-first diagnostics and replay evidence.\n",
                encoding="utf-8",
            )
            (root / "src" / "navigation").mkdir(parents=True)
            (root / "src" / "navigation" / "planner.py").write_text(
                "# Public component file name only.\n", encoding="utf-8"
            )
            (root / "docs" / "architecture" / "Private").mkdir()
            (root / "docs" / "architecture" / "Private" / "secret.md").write_text(
                "Emergency stop credentials and embedded navigation secrets.\n", encoding="utf-8"
            )

            facts = research.inspect_project(root)

        self.assertIn("ros2", facts["signals"])
        self.assertIn("navigation", facts["signals"])
        self.assertIn("safety", facts["signals"])
        self.assertIn("simulation", facts["signals"])
        self.assertIn("src", facts["top_level_directories"])
        self.assertIn("src/navigation/planner.py", facts["component_files"])
        self.assertNotIn("docs/architecture/Private/secret.md", facts["files_reviewed"])

    def test_inspect_project_excludes_external_symlinked_content(self) -> None:
        research = load_research_module()
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external_file = Path(outside) / "external.md"
            external_file.write_text("ROS 2 navigation private material.\n", encoding="utf-8")
            (root / "docs" / "architecture").mkdir(parents=True)
            linked_file = root / "docs" / "architecture" / "linked.md"
            try:
                linked_file.symlink_to(external_file)
            except OSError as error:
                self.skipTest(f"symbolic links are unavailable: {error}")

            facts = research.inspect_project(root)

        self.assertNotIn("docs/architecture/linked.md", facts["files_reviewed"])
        self.assertNotIn("navigation", facts["signals"])

    def test_rank_candidates_prefers_relevance_over_raw_stars(self) -> None:
        research = load_research_module()
        candidates = [
            {
                "full_name": "example/general-project",
                "html_url": "https://github.com/example/general-project",
                "description": "A general developer utility.",
                "topics": ["utility"],
                "stargazers_count": 50000,
                "updated_at": "2026-07-01T00:00:00Z",
                "archived": False,
                "private": False,
                "license": {"spdx_id": "Apache-2.0"},
            },
            {
                "full_name": "example/robot-navigation",
                "html_url": "https://github.com/example/robot-navigation",
                "description": "ROS 2 navigation, localization, and simulation tools.",
                "topics": ["robotics", "ros2", "navigation"],
                "stargazers_count": 3200,
                "updated_at": "2026-07-15T00:00:00Z",
                "archived": False,
                "private": False,
                "license": {"spdx_id": "Apache-2.0"},
            },
        ]

        ranked = research.rank_candidates(
            candidates,
            desired_terms=["robotics", "ros2", "navigation", "simulation"],
            minimum_stars=1000,
            as_of="2026-08-03T00:00:00Z",
        )

        self.assertEqual(ranked[0]["full_name"], "example/robot-navigation")
        self.assertTrue(ranked[0]["eligible"])
        self.assertGreater(ranked[0]["scores"]["relevance"], ranked[1]["scores"]["relevance"])

    def test_rank_candidates_rejects_archived_or_understarred_projects(self) -> None:
        research = load_research_module()
        candidates = [
            {
                "full_name": "example/old-robot",
                "html_url": "https://github.com/example/old-robot",
                "description": "ROS 2 navigation.",
                "topics": ["robotics", "ros2"],
                "stargazers_count": 5000,
                "updated_at": "2026-07-01T00:00:00Z",
                "archived": True,
                "private": False,
                "license": {"spdx_id": "Apache-2.0"},
            },
            {
                "full_name": "example/new-robot",
                "html_url": "https://github.com/example/new-robot",
                "description": "ROS 2 navigation.",
                "topics": ["robotics", "ros2"],
                "stargazers_count": 99,
                "updated_at": "2026-07-01T00:00:00Z",
                "archived": False,
                "private": False,
                "license": {"spdx_id": "Apache-2.0"},
            },
        ]

        ranked = research.rank_candidates(
            candidates,
            desired_terms=["robotics", "ros2"],
            minimum_stars=1000,
            as_of="2026-08-03T00:00:00Z",
        )

        self.assertFalse(ranked[0]["eligible"])
        self.assertIn("archived", ranked[0]["exclusions"])
        self.assertFalse(ranked[1]["eligible"])
        self.assertIn("below_minimum_stars", ranked[1]["exclusions"])

    def test_rank_candidates_rejects_non_github_candidate_source(self) -> None:
        research = load_research_module()
        ranked = research.rank_candidates(
            [
                {
                    "full_name": "example/robot-navigation",
                    "html_url": "https://untrusted.example/robot-navigation",
                    "description": "ROS 2 navigation.",
                    "topics": ["robotics", "ros2"],
                    "stargazers_count": 3200,
                    "updated_at": "2026-07-15T00:00:00Z",
                    "archived": False,
                    "private": False,
                    "license": {"spdx_id": "Apache-2.0"},
                }
            ],
            desired_terms=["robotics", "ros2"],
            minimum_stars=1000,
            as_of="2026-08-03T00:00:00Z",
        )

        self.assertFalse(ranked[0]["eligible"])
        self.assertIn("untrusted_source_url", ranked[0]["exclusions"])

    def test_rank_candidates_blocks_incomplete_or_zero_star_metadata_without_crashing(self) -> None:
        research = load_research_module()
        candidates = [
            {
                "full_name": "example/zero-stars",
                "html_url": "https://github.com/example/zero-stars",
                "description": "ROS 2 robotics navigation.",
                "topics": ["robotics"],
                "stargazers_count": 0,
                "updated_at": "2026-07-15T00:00:00Z",
                "archived": False,
                "private": False,
                "license": {"spdx_id": "Apache-2.0"},
            },
            {
                "full_name": "example/missing-metadata",
                "html_url": "https://github.com/example/missing-metadata",
                "description": "ROS 2 robotics navigation.",
                "topics": ["robotics"],
            },
        ]

        ranked = research.rank_candidates(
            candidates,
            desired_terms=["robotics", "ros2"],
            minimum_stars=1000,
            as_of="2026-08-03T00:00:00Z",
        )

        zero_stars = next(item for item in ranked if item["full_name"] == "example/zero-stars")
        missing = next(item for item in ranked if item["full_name"] == "example/missing-metadata")
        self.assertIn("below_minimum_stars", zero_stars["exclusions"])
        self.assertIn("missing_stargazers_count", missing["exclusions"])
        self.assertIn("missing_archived_status", missing["exclusions"])
        self.assertIn("missing_public_status", missing["exclusions"])
        self.assertIn("missing_updated_at", missing["exclusions"])
        self.assertIn("missing_license", missing["exclusions"])

    def test_rank_candidates_requires_an_architecture_match(self) -> None:
        research = load_research_module()
        ranked = research.rank_candidates(
            [
                {
                    "full_name": "example/general-project",
                    "html_url": "https://github.com/example/general-project",
                    "description": "A broadly useful tool.",
                    "topics": ["utility"],
                    "stargazers_count": 50000,
                    "updated_at": "2026-07-15T00:00:00Z",
                    "archived": False,
                    "private": False,
                    "license": {"spdx_id": "Apache-2.0"},
                }
            ],
            desired_terms=["robotics", "ros2"],
            minimum_stars=1000,
            as_of="2026-08-03T00:00:00Z",
        )

        self.assertFalse(ranked[0]["eligible"])
        self.assertIn("no_architecture_match", ranked[0]["exclusions"])

    def test_rank_candidates_requires_a_fixed_retrieval_timestamp(self) -> None:
        research = load_research_module()
        candidate = {
            "full_name": "example/robot-navigation",
            "html_url": "https://github.com/example/robot-navigation",
            "description": "ROS 2 robotics navigation.",
            "topics": ["robotics"],
            "stargazers_count": 3200,
            "updated_at": "2026-07-15T00:00:00Z",
            "archived": False,
            "private": False,
            "license": {"spdx_id": "Apache-2.0"},
        }

        first = research.rank_candidates(
            [candidate],
            desired_terms=["robotics", "ros2"],
            minimum_stars=1000,
            as_of="2026-08-03T00:00:00Z",
        )
        second = research.rank_candidates(
            [candidate],
            desired_terms=["robotics", "ros2"],
            minimum_stars=1000,
            as_of="2026-08-03T00:00:00Z",
        )

        self.assertEqual(first, second)
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            research.rank_candidates(
                [candidate], desired_terms=["robotics"], minimum_stars=1000, as_of=""
            )

    def test_github_request_rejects_unapproved_redirects(self) -> None:
        research = load_research_module()

        class RedirectedResponse:
            def __enter__(self) -> RedirectedResponse:
                return self

            def __exit__(self, *_: object) -> None:
                return None

            def geturl(self) -> str:
                return "https://untrusted.example/response"

            def read(self, _: int) -> bytes:
                return b"{}"

        with (
            patch.object(research, "urlopen", return_value=RedirectedResponse()),
            self.assertRaisesRegex(RuntimeError, "redirect"),
        ):
            research._github_request("https://api.github.com/search/repositories?q=robotics")

    def test_readme_evidence_uses_canonical_source_and_escapes_untrusted_headings(self) -> None:
        research = load_research_module()
        content = "# [Unexpected](javascript:alert(1)) | heading\nROS 2 navigation\n"
        response = {
            "encoding": "base64",
            "content": research.base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "html_url": "https://untrusted.example/not-used",
        }
        with patch.object(research, "_github_request", return_value=response):
            evidence = research.readme_evidence("example/robot-navigation")
        report = research.render_recommendation_report(
            project_facts={"signals": ["ros2", "navigation"]},
            ranked_candidates=[],
            generated_at="2026-08-03T00:00:00Z",
            architecture_evidence=[{**evidence, "retrieved_at": "2026-08-03T00:00:00Z"}],
        )

        self.assertEqual(evidence["source_url"], "https://github.com/example/robot-navigation")
        self.assertIn("\\[Unexpected\\]", report)
        self.assertNotIn("[Unexpected](javascript", report)

    def test_research_persists_local_facts_when_public_discovery_is_blocked(self) -> None:
        research = load_research_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "research"
            (root / "README.md").write_text("ROS 2 robot navigation.\n", encoding="utf-8")
            arguments = SimpleNamespace(
                project_root=root,
                output_dir=output_dir,
                minimum_stars=1000,
                candidate_limit=10,
                query=None,
                readme_limit=3,
                as_of="2026-08-03T00:00:00Z",
            )
            with (
                patch.object(
                    research,
                    "search_github_repositories",
                    side_effect=RuntimeError("rate limited"),
                ),
                self.assertRaisesRegex(RuntimeError, "project facts"),
            ):
                research._run_research(arguments)

            facts = json.loads((output_dir / "project-facts.json").read_text(encoding="utf-8"))
            self.assertEqual(facts["retrieved_at"], "2026-08-03T00:00:00Z")
            self.assertTrue((output_dir / "research-blocker.md").is_file())

    def test_render_report_records_sources_and_no_copy_boundary(self) -> None:
        research = load_research_module()
        report = research.render_recommendation_report(
            project_facts={"signals": ["robotics", "ros2", "navigation"]},
            ranked_candidates=[
                {
                    "full_name": "example/robot-navigation",
                    "html_url": "https://github.com/example/robot-navigation",
                    "description": "ROS 2 navigation.",
                    "stargazers_count": 3200,
                    "updated_at": "2026-07-15T00:00:00Z",
                    "license": "Apache-2.0",
                    "eligible": True,
                    "exclusions": [],
                    "matched_terms": ["robotics", "ros2", "navigation"],
                    "scores": {
                        "total": 88.0,
                        "relevance": 50.0,
                        "popularity": 18.0,
                        "freshness": 15.0,
                        "health": 5.0,
                    },
                }
            ],
            generated_at="2026-08-03T00:00:00Z",
            architecture_evidence=[
                {
                    "repository": "example/robot-navigation",
                    "source_url": "https://github.com/example/robot-navigation",
                    "signals": ["ros2", "navigation"],
                    "headings": ["Architecture", "Simulation"],
                }
            ],
        )

        self.assertIn("https://github.com/example/robot-navigation", report)
        self.assertIn("Do not copy implementation code", report)
        self.assertIn("Open decisions", report)
        self.assertIn("Candidate architecture evidence", report)

    def test_inspect_command_writes_only_project_facts(self) -> None:
        research = load_research_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "research" / "project-facts.json"
            (root / "README.md").write_text("ROS 2 robot navigation.\n", encoding="utf-8")

            exit_code = research.main(
                ["inspect", "--project-root", str(root), "--output", str(output)]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.is_file())
            self.assertIn("navigation", output.read_text(encoding="utf-8"))

    def test_rank_command_supports_a_tool_collected_candidate_fixture(self) -> None:
        research = load_research_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            facts_path = root / "facts.json"
            candidates_path = root / "candidates.json"
            output_dir = root / "research"
            facts_path.write_text(
                json.dumps({"signals": ["robotics", "ros2", "navigation"]}), encoding="utf-8"
            )
            candidates_path.write_text(
                json.dumps(
                    [
                        {
                            "full_name": "example/robot-navigation",
                            "html_url": "https://github.com/example/robot-navigation",
                            "description": "ROS 2 navigation.",
                            "topics": ["robotics", "ros2", "navigation"],
                            "stargazers_count": 3200,
                            "updated_at": "2026-07-15T00:00:00Z",
                            "archived": False,
                            "private": False,
                            "license": {"spdx_id": "Apache-2.0"},
                        }
                    ]
                ),
                encoding="utf-8",
            )

            exit_code = research.main(
                [
                    "rank",
                    "--project-facts",
                    str(facts_path),
                    "--candidates",
                    str(candidates_path),
                    "--output-dir",
                    str(output_dir),
                    "--as-of",
                    "2026-08-03T00:00:00Z",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "ranked-candidates.json").is_file())
            self.assertTrue((output_dir / "architecture-research.md").is_file())

    def test_research_command_writes_readme_evidence_from_public_candidates(self) -> None:
        research = load_research_module()
        candidate = {
            "full_name": "example/robot-navigation",
            "html_url": "https://github.com/example/robot-navigation",
            "description": "ROS 2 navigation.",
            "topics": ["robotics", "ros2", "navigation"],
            "stargazers_count": 3200,
            "updated_at": "2026-07-15T00:00:00Z",
            "archived": False,
            "private": False,
            "license": {"spdx_id": "Apache-2.0"},
        }
        evidence = {
            "repository": "example/robot-navigation",
            "source_url": "https://github.com/example/robot-navigation",
            "signals": ["ros2", "navigation"],
            "headings": ["Architecture"],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "research"
            (root / "README.md").write_text("ROS 2 robot navigation.\n", encoding="utf-8")
            with (
                patch.object(research, "search_github_repositories", return_value=[candidate]),
                patch.object(research, "readme_evidence", return_value=evidence),
            ):
                exit_code = research.main(
                    [
                        "research",
                        "--project-root",
                        str(root),
                        "--output-dir",
                        str(output_dir),
                    ]
                )

            report = (output_dir / "architecture-research.md").read_text(encoding="utf-8")
            self.assertEqual(exit_code, 0)
            self.assertIn("Candidate architecture evidence", report)
            self.assertIn("example/robot-navigation", report)


if __name__ == "__main__":
    unittest.main()
