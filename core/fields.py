from django.db.models import BooleanField


class PrimaryBooleanField(BooleanField):
    def __init__(self, *args, **kwargs):
        self.filter_on = kwargs.pop('filter_on')
        kwargs['default'] = False
        super(PrimaryBooleanField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(PrimaryBooleanField, self).deconstruct()
        kwargs["filter_on"] = None
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        objects = model_instance.__class__.objects.filter(**{self.filter_on: getattr(model_instance, self.filter_on)})

        if model_instance.pk:
            objects = objects.exclude(pk=model_instance.pk)

        # If True then set all others as False
        if getattr(model_instance, self.attname):
            objects.update(**{self.attname: False})
        # If no true object exists that isnt saved model, save as True
        elif not objects.filter(**{self.attname: True}).exists():
            setattr(model_instance, self.attname, True)
        return getattr(model_instance, self.attname)
