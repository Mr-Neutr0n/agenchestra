"""I-421: Cursor `subagent_type`/`subagent_id` alanları hook.py'nin okuduğu `agent_type`/`agent_id` olur;
Claude'un kendi alanları ezilmez; alt ajan alanı olmayan olaylara alan eklenmez."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import cursor_hook as C  # noqa: E402


class CursorRol(unittest.TestCase):
    def test_subagent_start_rol_alanlari_eslenir(self):
        c = C.girdi_donustur("subagentStart", {"subagent_type": "denetci", "subagent_id": "s-1", "task": "t",
                                               "workspace_roots": ["/C:/proje"]})
        self.assertEqual(c["agent_type"], "denetci")
        self.assertEqual(c["agent_id"], "s-1")
        self.assertTrue(str(c.get("agent_type")).endswith("denetci"))  # hook.py:1432 koşulu

    def test_subagent_stop_tur_eslenir(self):
        self.assertEqual(C.girdi_donustur("subagentStop", {"subagent_type": "explore"})["agent_type"], "explore")

    def test_claude_alani_ezilmez(self):
        c = C.girdi_donustur("subagentStart", {"agent_type": "orkestra:denetci", "subagent_type": "x"})
        self.assertEqual(c["agent_type"], "orkestra:denetci")

    def test_arac_olayinda_alan_eklenmez(self):
        c = C.girdi_donustur("preToolUse", {"tool_name": "Write", "tool_input": {"file_path": "a"}})
        self.assertNotIn("agent_type", c)
        self.assertNotIn("agent_id", c)


if __name__ == "__main__":
    unittest.main()
