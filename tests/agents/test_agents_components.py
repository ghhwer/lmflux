import unittest
from lmflux.agents.components import AgentRef, Context

class TestAgentRef(unittest.TestCase):
    def test_init(self):
        agent = object()  # Mock agent object
        agent_ref = AgentRef("test_agent", agent)
        self.assertEqual(agent_ref.agent_id, "test_agent")
        self.assertEqual(agent_ref.agent, agent)

    def test_get_agent(self):
        agent = object()  # Mock agent object
        agent_ref = AgentRef("test_agent", agent)
        self.assertEqual(agent_ref.get_agent(), agent)

    def test_str(self):
        agent = object()  # Mock agent object
        agent_ref = AgentRef("test_agent", agent)
        self.assertEqual(str(agent_ref), "AGENT_REF[test_agent]")

class TestContext(unittest.TestCase):
    def test_init(self):
        context = Context({}, {})
        self.assertEqual(context.context, {})
        self.assertEqual(context.context_cumulative, {})

    def test_set(self):
        context = Context({}, {})
        context.set("key", "value")
        self.assertEqual(context.get("key"), "value")

    def test_remove(self):
        context = Context({"key": "value"}, {})
        context.remove("key")
        self.assertNotIn("key", context.context)

    def test_get(self):
        context = Context({"key": "value"}, {})
        self.assertEqual(context.get("key"), "value")
        self.assertIsNone(context.get("nonexistent_key"))

    def test_get_context(self):
        context = Context({"key": "value"}, {})
        self.assertEqual(context.get_context(), {"key": "value"})

    def test_set_cumulative(self):
        context = Context({}, {})
        context.set_cumulative("key", "value")
        self.assertEqual(context.get_cumulative("key"), ["value"])

    def test_get_cumulative(self):
        context = Context({}, {})
        context.set_cumulative("key", "value")
        self.assertEqual(context.get_cumulative("key"), ["value"])

if __name__ == '__main__':
    unittest.main()