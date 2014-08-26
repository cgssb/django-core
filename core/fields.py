from django.db.models import BooleanField


class PrimaryBooleanField(BooleanField):
    """
    Extends models.BooleanField to only allow one True value per Model instances (filtered on filter_on)::

      class Email(CoreModel):
          person = models.ForeignKey(Person, related_name='emails')
          email = models.EmailField()
          is_primary = PrimaryBooleanField(filter_on='person')

      >>> p = Person.objects.create(first_name='Darth', last_name='Vader')
      >>> email1 = p.emails.create(email='darth@outlook.com')
      >>> email1.is_primary
      True
      >>> email2 = p.emails.create(email='vader@outlook.com')
      >>> email2.is_primary
      False
      >>> email2.is_primary = True
      >>> email2.save()
      >>> Email.objects.get(person=p, email='darth@outlook.com').is_primary
      False

    if person only has one Email is_primary will be True

    if person is_primary = True then all other person emails is_primary == False
    
    """
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
