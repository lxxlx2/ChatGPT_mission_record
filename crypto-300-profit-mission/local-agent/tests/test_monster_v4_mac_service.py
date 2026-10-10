"""Monster isolated macOS launchd deployment contract, no live install."""
import importlib.util
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "scripts/monster_v4_mac_service.py"
spec = importlib.util.spec_from_file_location("monster_v4_mac_service", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MonsterMacServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.root=self.dir/"MonsterV4"
        self.plist=self.dir/"LaunchAgents"/"monster.plist"
        self.source=self.dir/"source"
        self.source.mkdir()
        for name in m.SCRIPT_NAMES:
            (self.source/name).write_text("print('independent module')\n",
                                          encoding="utf-8")

    def test_plist_separates_frank_paths_and_disables_mail(self):
        release=self.root/"releases"/"id"/m.SCRIPT_NAMES[0]
        plan=m.service_plist(Path("/opt/python/bin/python3"),release,
                             self.root/"state/monster.sqlite",self.root/"logs")
        self.assertEqual(plan["Label"],m.LABEL)
        self.assertTrue(plan["KeepAlive"])
        self.assertEqual(plan["ProgramArguments"][-4:],
            ["--db",str(self.root/"state/monster.sqlite"),
             "--interval-seconds","180"])
        self.assertNotIn("Frank",str(plan))
        self.assertNotIn("8766",str(plan))
        self.assertNotIn("SMTP",str(plan))
        self.assertEqual(plistlib.loads(plistlib.dumps(plan))["Label"],m.LABEL)

    def test_dry_run_stages_isolated_release_without_launch(self):
        with patch.object(m.sys,"platform","darwin"),\
             patch.object(m,"source_files",return_value=[
                 self.source/name for name in m.SCRIPT_NAMES]),\
             patch.object(m,"run_launchctl") as launch:
            out=m.install(self.root,self.plist,do_launch=False)
        self.assertEqual(out["result"],"DRY_RUN")
        self.assertFalse(self.plist.exists())
        self.assertTrue((self.root/"releases"/out["release"]/
                         m.SCRIPT_NAMES[0]).is_file())
        self.assertFalse((self.root/"state/monster.sqlite").exists())
        launch.assert_not_called()

    def test_foreign_plist_refused_without_mutation(self):
        self.plist.parent.mkdir(parents=True)
        before=plistlib.dumps({"Label":"com.someone.frank.service"})
        self.plist.write_bytes(before)
        with patch.object(m.sys,"platform","darwin"),\
             patch.object(m,"source_files",return_value=[
                 self.source/name for name in m.SCRIPT_NAMES]):
            with self.assertRaisesRegex(ValueError,"FOREIGN_PLIST_REFUSED"):
                m.install(self.root,self.plist,do_launch=False)
        self.assertEqual(self.plist.read_bytes(),before)

    def test_uninstall_only_own_plist_and_preserves_state(self):
        self.plist.parent.mkdir(parents=True)
        self.plist.write_bytes(plistlib.dumps({"Label":m.LABEL}))
        (self.root/"state").mkdir(parents=True)
        evidence=self.root/"state"/"monster.sqlite"
        evidence.write_text("do-not-delete",encoding="utf-8")
        with patch.object(m.sys,"platform","darwin"),\
             patch.object(m,"inspect",return_value={"status":"INSTALLED_NOT_LOADED"}),\
             patch.object(m,"run_launchctl") as launch:
            out=m.uninstall(self.root,self.plist)
        self.assertEqual(out["result"],"REMOVED_SERVICE_ONLY")
        self.assertFalse(self.plist.exists())
        self.assertEqual(evidence.read_text(),"do-not-delete")
        launch.assert_not_called()

    def test_platform_protection(self):
        with patch.object(m.sys,"platform","linux"):
            with self.assertRaisesRegex(RuntimeError,"MACOS"):
                m.install(self.root,self.plist)
            with self.assertRaisesRegex(RuntimeError,"MACOS"):
                m.uninstall(self.root,self.plist)

    def test_inspect_never_mutates_database_when_missing(self):
        result=m.inspect(self.root,self.plist)
        self.assertEqual(result["status"],"NOT_INSTALLED")
        self.assertFalse((self.root/"state/monster.sqlite").exists())


if __name__=="__main__":
    unittest.main()
