"""Offline regression for PR versus manual workflow_dispatch immutable SHA checkout.

Exercises the shell step from the actual YAML, with a fake git executable.
Does not request, dispatch, or modify GitHub Actions executions.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

WORKFLOW = (Path(__file__).resolve().parents[2] /
            ".github/workflows/bsc-meme-address-model-v1-tests.yml")
EXPR = "${{ github.event.pull_request.head.sha || github.sha }}"
STEP = "      - name: Assert checked-out source SHA on PR or manual dispatch"
A = "a" * 40
B = "b" * 40
C = "c" * 40


def workflow_script():
    content = WORKFLOW.read_text(encoding="utf-8")
    assert "  workflow_dispatch:" in content
    assert "  pull_request:" in content
    assert f"          ref: {EXPR}" in content
    assert f"          REVIEWED_HEAD_SHA: {EXPR}" in content
    assert "          EVENT_PR_HEAD_SHA: ${{ github.event.pull_request.head.sha }}" in content
    assert "          EVENT_SHA: ${{ github.sha }}" in content
    assert "          EVENT_NAME: ${{ github.event_name }}" in content
    lines = content.splitlines()
    start = lines.index(STEP)
    run = lines.index("        run: |", start)
    end = next((i for i in range(run+1, len(lines))
                if lines[i].startswith("      - name: ")), len(lines))
    script = "\n".join(line[10:] if line.startswith("          ") else line
                       for line in lines[run+1:end])
    assert "test \"$(git rev-parse HEAD)\" = \"$REVIEWED_HEAD_SHA\" || exit 1" in script
    return script


def run_identity(event, pr_head, event_sha, checked_out_sha, expected):
    with tempfile.TemporaryDirectory(prefix="bsc-workflow-sha-") as tmp:
        fake = Path(tmp) / "git"
        fake.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = rev-parse ] && [ "$2" = HEAD ]; then\n'
            '  printf "%s\\n" "$MOCK_CHECKOUT_SHA"\n'
            "else\n"
            "  exit 3\n"
            "fi\n",
            encoding="utf-8",
        )
        fake.chmod(0o700)
        env = os.environ.copy()
        env.update({
            "PATH": tmp + os.pathsep + os.environ.get("PATH", ""),
            "EVENT_NAME": event,
            "EVENT_PR_HEAD_SHA": pr_head,
            "EVENT_SHA": event_sha,
            "REVIEWED_HEAD_SHA": pr_head or event_sha,
            "MOCK_CHECKOUT_SHA": checked_out_sha,
        })
        result = subprocess.run(
            ["bash", "-c", workflow_script()],
            capture_output=True, text=True, env=env, check=False,
        )
    assert (result.returncode == 0) == expected, (
        f"Unexpected identity result for {event}: rc={result.returncode}; "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )


class WorkflowEventIdentityTests(unittest.TestCase):
    def test_real_pr_head_overrides_synthetic_merge_sha(self):
        run_identity("pull_request", A, B, A, True)

    def test_manual_dispatch_selected_branch_sha(self):
        run_identity("workflow_dispatch", "", C, C, True)

    def test_missing_pr_head_cannot_silently_use_merge_sha(self):
        run_identity("pull_request", "", B, B, False)

    def test_pr_merge_sha_checkout_rejected(self):
        run_identity("pull_request", A, B, B, False)

    def test_manual_wrong_checkout_sha_rejected(self):
        run_identity("workflow_dispatch", "", C, B, False)

    def test_unknown_event_rejected_even_if_sha_matches(self):
        run_identity("push", "", C, C, False)

    def test_manual_sha_missing_is_rejected(self):
        run_identity("workflow_dispatch", "", "", "", False)

    def test_manual_event_cannot_carry_pr_head(self):
        run_identity("workflow_dispatch", A, C, A, False)

    def test_sha_guards_explicit_exit_on_failure_on_any_bash(self):
        script = workflow_script()
        required = (
            '[[ "$REVIEWED_HEAD_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 1',
            '[[ "$EVENT_PR_HEAD_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 1',
            '[[ "$EVENT_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 1',
            'test "$REVIEWED_HEAD_SHA" = "$EVENT_PR_HEAD_SHA" || exit 1',
            'test "$REVIEWED_HEAD_SHA" = "$EVENT_SHA" || exit 1',
            'test -z "$EVENT_PR_HEAD_SHA" || exit 1',
            'test "$(git rev-parse HEAD)" = "$REVIEWED_HEAD_SHA" || exit 1',
        )
        for check in required:
            with self.subTest(check=check):
                self.assertIn(check, script)

    def test_invalid_manual_sha_shape_rejected(self):
        for invalid in ("not-a-sha", "f" * 39, "F" * 40, "f" * 41):
            with self.subTest(invalid=invalid):
                run_identity("workflow_dispatch", "", invalid, invalid, False)


if __name__ == "__main__":
    unittest.main()
