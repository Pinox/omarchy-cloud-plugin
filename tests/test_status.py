#!/usr/bin/env python3

import importlib.util
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import mock_open, patch


STATUS_PATH = Path(__file__).resolve().parents[1] / "bin" / "omarchy-cloud-status"
LOADER = SourceFileLoader("omarchy_cloud_status", str(STATUS_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
status = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(status)


class FailedMountStatusTests(unittest.TestCase):
    def test_reads_failure_from_selected_legacy_unit(self):
        systemctl_output = """\
Id=omarchy-cloud-mount@gdrive.service
ActiveState=inactive
UnitFileState=disabled

Id=rclone-mount@gdrive.service
ActiveState=failed
UnitFileState=enabled
"""
        commands = []

        def fake_run(command, timeout=5):
            commands.append(command)
            if command[0] == "systemctl":
                return 0, systemctl_output
            if command[0] == "journalctl":
                return 0, "ERROR : mount failed"
            self.fail(f"unexpected command: {command}")

        with patch.object(status, "run", side_effect=fake_run):
            unit = status.unit_states(["gdrive"])["gdrive"]
            detail = status.last_failure(unit["unit"])

        self.assertEqual(unit["active"], "failed")
        self.assertEqual(unit["unit"], "rclone-mount@gdrive.service")
        self.assertEqual(detail, "ERROR : mount failed")
        self.assertEqual(
            commands[1][0:5],
            [
                "journalctl",
                "--user",
                "-u",
                "rclone-mount@gdrive.service",
                "-n",
            ],
        )


class MountInfoTests(unittest.TestCase):
    def test_preserves_utf8_and_decodes_only_kernel_octal_escapes(self):
        mountinfo = (
            "36 29 0:42 / /tmp/Café/My\\040Drive rw,nosuid,nodev "
            "- fuse.rclone gdrive: rw\n"
        )

        with patch("builtins.open", mock_open(read_data=mountinfo)):
            paths = status.mounted_paths()

        self.assertEqual(paths, {"/tmp/Café/My Drive"})


class RemoteDiscoveryTests(unittest.TestCase):
    def test_separates_existing_remotes_without_returning_secrets(self):
        config = """\
[owned]
type = onedrive
token = encrypted-owned-token

[existing]
type = onedrive
token = encrypted-existing-token

[not-a-valid-remote!]
type = onedrive
token = encrypted-invalid-token
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rclone.conf"
            path.write_text(config, encoding="utf-8")

            managed, unmanaged = status.read_remote_groups(path, {"owned"})

        self.assertEqual([remote["name"] for remote in managed], ["owned"])
        self.assertEqual([remote["name"] for remote in unmanaged], ["existing"])
        self.assertTrue(unmanaged[0]["hasAuth"])
        self.assertNotIn("token", unmanaged[0])
        self.assertEqual(unmanaged[0]["type"], "onedrive")


if __name__ == "__main__":
    unittest.main()
