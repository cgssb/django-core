from django.db import models
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django_extensions.db import fields as djefields
import datetime
import os
import uuid

def uuid_upload_to(dirname):
    """ Give an uploaded file a nice generic uuid filename """
    def func(instance, filename):
        ext = filename.split('.')[-1].lower()
        filename = "%s.%s" % (uuid.uuid4(), ext)
        return os.path.join(dirname, filename)
    return func

class CoreQuerySet(models.query.QuerySet):
    def published(self):
        """
        File for objects where is_published=True
        """
        return self.filter(is_published=True)

    def unpublished(self):
        """
        File for objects where is_published=False
        """
        return self.filter(is_published=False)

    def valid(self):
        """
        File for objects where is_valid=True
        """
        return self.filter(is_valid=True)

    def invalid(self):
        """
        File for objects where is_valid=False
        """
        return self.filter(is_valid=False)

    def active(self):
        """
        File for objects where is_active=True
        """
        return self.filter(is_active=True)

    def inactive(self):
        """
        File for objects where is_active=False
        """
        return self.filter(is_active=False)

    def get_current(self, begin_field='date_begin', end_field='date_end', as_of=None):
        return self.current(begin_field, end_field, as_of).get()

    def current(self, begin_field='date_begin', end_field='date_end', as_of=None):
        """ 
        Filter for objects where as_of falls between begin_field, end_field.
        begin_field -> inclusive
        end_field -> not inclusive
        begin_field and end_field can be None
        """
        if as_of is None:
            as_of = datetime.datetime.now()

        has_no_begin_date = models.Q(**{ '%s__isnull' % (begin_field): True})
        begin_before_date = models.Q(**{ '%s__lte' % (begin_field,): as_of })
        has_no_end = models.Q(**{ '%s__isnull' % (end_field,): True})
        end_after_date = models.Q(**{ '%s__gt' % (end_field,): as_of })

        q = (has_no_begin_date | begin_before_date) & (has_no_end | end_after_date)
        return self.filter(q) 

    def future(self, begin_field='date_begin', end_field='date_end', as_of=None):
        """ 
        Filter for objects that have not begun yet.
        """
        if as_of is None:
            as_of = datetime.datetime.now()

        has_begin_date = models.Q(**{ '%s__isnull' % (begin_field): False})
        begin_after_date = models.Q(**{ '%s__gt' % (begin_field,): as_of })

        q = has_begin_date & begin_after_date
        return self.filter(q)

    def past(self, begin_field='date_begin', end_field='date_end', as_of=None):
        """ 
        Filter for objects that have ended.
        """
        if as_of is None:
            as_of = datetime.datetime.now()

        has_end_date = models.Q(**{ '%s__isnull' % (end_field): False})
        end_before_date = models.Q(**{ '%s__lte' % (end_field,): as_of })

        q = has_end_date & end_before_date
        return self.filter(q)


class CoreModel(models.Model):
    """ 
    Abstract model that provides a uuid key and created/modified timestamps.
    """
    created = djefields.CreationDateTimeField(auto_now_add=True)
    modified = djefields.ModificationDateTimeField(auto_now=True)
    key = djefields.UUIDField()

    objects = CoreQuerySet.as_manager()

    def has_changed(self, field):
        """
        Check to see if the value of field in DB is different than the value in instance.
        """
        if not self.pk: return True
        instance_value = getattr(self, field)
        try:
            old_value = getattr(self.__class__._default_manager.get(pk=self.pk), field)
        except self.__class__.DoesNotExist:
            old_value = None

        return instance_value != old_value
        
    class Meta:
        get_latest_by = 'created'
        abstract = True


class HistoryCoreModel(CoreModel):
    date_begin = models.DateField(blank=True, null=True)
    date_end = models.DateField(blank=True, null=True)

    class Meta(CoreModel.Meta):
        abstract = True

    def clean(self):
        if self.date_begin and self.date_end:
            if self.date_end < self.date_begin:
                raise ValidationError("Can't have a begin date AFTER an end date")
        f = { self.history_key: getattr(self, self.history_key) }
        full_history = self.__class__._default_manager.filter(**f)
        if self.pk:
            full_history = full_history.exclude(pk=self.pk)
        if full_history.current(as_of=self.date_begin).exists() or full_history.current(as_of=self.date_end).exists():
            raise ValidationError("Can't have overlapping history dates for %s" % self)

