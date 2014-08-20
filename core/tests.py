from django.test import TestCase

class CoreTestCase(TestCase):

    def char_has_changed(self, obj, field, is_new=True):
        if is_new:
            self.assertEqual(obj.pk, None)
            self.assertTrue(obj.has_changed(field))
            obj.save()

        self.assertFalse(obj.has_changed(field))

        setattr(obj, field, getattr(obj, field) + 'asdf')
        self.assertTrue(obj.has_changed(field))

