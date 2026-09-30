import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ClientPackageTests(unittest.TestCase):
    def test_codex_marketplace_points_to_oauth_plugin(self):
        marketplace = read_json(".agents/plugins/marketplace.json")
        self.assertEqual(marketplace["name"], "paper-view-mcp")
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "paper-view-canvas")
        self.assertEqual(entry["source"]["path"], "./plugins/paper-view-canvas")
        plugin = read_json("plugins/paper-view-canvas/.codex-plugin/plugin.json")
        self.assertEqual(plugin["interface"]["displayName"], "Paper View Board")
        self.assertTrue((ROOT / "plugins/paper-view-canvas" / plugin["interface"]["logo"]).is_file())
        mcp = read_json("plugins/paper-view-canvas/.mcp.json")
        self.assertEqual(mcp["mcpServers"]["paper-view-canvas"]["url"], "https://ipaperview.com/mcp")
        self.assertEqual(mcp["mcpServers"]["paper-view-canvas"]["auth"], "oauth")

    def test_workbuddy_uses_the_same_oauth_endpoint(self):
        connector = ROOT / "integrations/workbuddy/paper-view-canvas"
        meta = read_json("integrations/workbuddy/paper-view-canvas/connector-meta.json")
        config = read_json("integrations/workbuddy/paper-view-canvas/mcp.json")
        server = config["mcpServers"]["paper-view-canvas"]
        self.assertEqual(meta["name_en"], "Paper View Board")
        self.assertNotIn("auth_mode", meta)
        self.assertEqual(server["type"], "streamableHttp")
        self.assertEqual(server["url"], "https://ipaperview.com/mcp")
        self.assertNotIn("headers", server)
        self.assertFalse((connector / "token-schema.json").exists())
        self.assertTrue((connector / "icon.svg").is_file())


if __name__ == "__main__":
    unittest.main()
