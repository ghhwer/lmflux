import unittest
from lmflux.core.templates import Templates
import tempfile
import os

class TestTemplates(unittest.TestCase):

    def setUp(self):
        self.template_manager = Templates()
        self.template_manager.clear()
        self.temp_dir = tempfile.mkdtemp()
        self.template_manager.set_location(self.temp_dir)
        self.template_manager.put_template("to_ignore_persist", "ignore_template", persistent=True)
        self.template_manager.put_template("to_ignore_persist_delete", "ignore_template", persistent=True)

    def tearDown(self):
        self.template_manager.clear()
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)

    def test_init(self):
        self.assertEqual(self.template_manager._Templates__inmem_templates, {})
        self.assertEqual(self.template_manager._Templates__ignore_template_id, [])
        self.assertEqual(self.template_manager._Templates__external_location, self.temp_dir)
        self.assertFalse(self.template_manager._Templates__allow_external_deletion)

    def test_put_template_in_memory(self):
        template_id = "test.template"
        template_src = "This is a test template"
        self.template_manager.put_template(template_id, template_src)
        self.assertIn(template_id, self.template_manager._Templates__inmem_templates)
        self.assertEqual(self.template_manager._Templates__inmem_templates[template_id], template_src)

    def test_put_template_persistent(self):
        template_id = "test.template"
        template_src = "This is a persistent test template"
        self.template_manager.put_template(template_id, template_src, persistent=True)
        # Check if the file is created in the external location
        template_path = template_id.split('.')
        path = '/'.join(template_path[:-1])
        file_path = f'{self.temp_dir}/{path}/{template_path[-1]}.md'
        print(file_path)
        self.assertTrue(os.path.isfile(file_path))
        with open(file_path, 'r') as f:
            self.assertEqual(f.read(), template_src)

    def test_get_template_in_memory(self):
        template_id = "test.template"
        template_src = "This is a test template"
        self.template_manager.put_template(template_id, template_src)
        retrieved_template = self.template_manager.get_template(template_id)
        self.assertEqual(retrieved_template, template_src)

    def test_get_template_persistent(self):
        template_id = "test.template"
        template_src = "This is a persistent test template"
        self.template_manager.put_template(template_id, template_src, persistent=True)
        retrieved_template = self.template_manager.get_template(template_id)
        self.assertEqual(retrieved_template, template_src)

    def test_delete_template_in_memory(self):
        template_id = "test.template"
        template_src = "This is a test template"
        self.template_manager.put_template(template_id, template_src)
        self.template_manager.delete_template(template_id)
        self.assertNotIn(template_id, self.template_manager._Templates__inmem_templates)

    def test_delete_template_persistent(self):
        template_id = "test.template"
        template_src = "This is a persistent test template"
        self.template_manager.put_template(template_id, template_src, persistent=True)
        self.template_manager.set_allow_external_deletion(True)
        self.template_manager.delete_template(template_id)
        template_path = template_id.split('.')
        path = '/'.join(template_path[:-1])
        file_path = f'{self.temp_dir}/{path}/{template_path[-1]}.md'
        self.assertFalse(os.path.isfile(file_path))

    def test_get_with_context(self):
        template_id = "test.template"
        template_src = "Hello {{name}}"
        self.template_manager.put_template(template_id, template_src)
        context = {"name": "World"}
        result = self.template_manager.get_with_context(template_id, context)
        self.assertEqual(result, "Hello World")
    
    def test_get_after_delete_soft(self):
        self.template_manager.set_soft_external_delete()
        result = self.template_manager.get_template("to_ignore_persist")
        self.assertEqual(result, "ignore_template")
        self.template_manager.delete_template("to_ignore_persist")
        self.assertRaises(AttributeError, self.template_manager.get_template, "to_ignore_persist")
        assert os.path.isfile(self.temp_dir+'/to_ignore_persist.md') 
    
    def test_get_after_delete_hard(self):
        self.template_manager.set_hard_external_delete()
        result = self.template_manager.get_template("to_ignore_persist_delete")
        self.assertEqual(result, "ignore_template")
        self.template_manager.delete_template("to_ignore_persist")
        self.assertRaises(AttributeError, self.template_manager.get_template, "to_ignore_persist")
        assert not os.path.isfile(self.temp_dir+'/to_ignore_persist.md') 
        self.template_manager.set_soft_external_delete()

if __name__ == '__main__':
    unittest.main()