import unittest
from lmflux.agents.sessions import Context, Session

class TestContext(unittest.TestCase):
    def test_init(self):
        context = Context()
        self.assertEqual(context.context, {})
        self.assertEqual(context.context_cumulative, {})

    def test_clone_context(self):
        original_context = Context()
        original_context.set("key", "value")
        context = Context()
        context.clone_context(original_context)
        self.assertEqual(context.context, {"key": "value"})

    def test_set(self):
        context = Context()
        context.set("key", "value")
        self.assertEqual(context.get("key"), "value")

    def test_remove(self):
        context = Context()
        context.set("key", "value")
        context.remove("key")
        self.assertNotIn("key", context.context)

    def test_get(self):
        context = Context()
        context.set("key", "value")
        self.assertEqual(context.get("key"), "value")
        self.assertIsNone(context.get("nonexistent_key"))

    def test_get_context(self):
        context = Context()
        context.set("key", "value")
        self.assertEqual(context.get_context(), {"key": "value"})

    def test_set_cumulative(self):
        context = Context()
        context.set_cumulative("key", "value")
        self.assertEqual(context.get_cumulative("key"), ["value"])

    def test_get_cumulative(self):
        context = Context()
        context.set_cumulative("key", "value")
        self.assertEqual(context.get_cumulative("key"), ["value"])

class TestSession(unittest.TestCase):
    def test_init(self):
        session = Session()
        self.assertIsNotNone(session.session_id)

    def test_init_with_starting_context(self):
        starting_context = Context()
        starting_context.set("key", "value")
        session = Session(starting_context)
        self.assertEqual(session.context_as_dict(), {"key": "value"})

if __name__ == '__main__':
    unittest.main()