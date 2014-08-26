from django.db import models
from django.core.exceptions import ValidationError
from localflavor.us.models import USStateField
from django_extensions.db import fields as djefields
import datetime
import os
import uuid

def uuid_upload_to(dirname):
    """ 
    Give an uploaded file a nice generic uuid filename 
    """
    def func(instance, filename):
        ext = filename.split('.')[-1].lower()
        filename = "%s.%s" % (uuid.uuid4(), ext)
        return os.path.join(dirname, filename)
    return func

class CoreQuerySet(models.query.QuerySet):
    """ 
    A few enahancements from the stock ModelManager.

    Esp.  get_current(), current(), past(), and future()
    """
    def published(self):
        """
        Only objects that is_published=True
        """
        return self.filter(is_published=True)

    def unpublished(self):
        """
        Only objects that is_published=False
        """
        return self.filter(is_published=False)

    def valid(self):
        """
        Only objects that is_valid=True
        """
        return self.filter(is_valid=True)

    def invalid(self):
        """
        Only objects that is_valid=False
        """
        return self.filter(is_valid=False)

    def active(self):
        """
        Only objects that is_active=True
        """
        return self.filter(is_active=True)

    def inactive(self):
        """
        Only objects that is_active=False
        """
        return self.filter(is_active=False)

    def get_current(self, begin_field='date_begin', end_field='date_end', as_of=None):
        """
        Return the queryset object whose as_of date falls between begin_field, end_field 

        This assumes there is no overlap in begin,end ranges

        """
        return self.current(begin_field, end_field, as_of).get()

    def current(self, begin_field='date_begin', end_field='date_end', as_of=None):
        """ 
        Filter for objects where as_of falls between begin_field (inclusive), end_field (not exclusive).

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


class HistoryModel(models.Model):
    """
    Abstract model that includes (optional, non-overlapping) date_begin and date_end fields::

      date_begin = models.DateField(blank=True, null=True)
      date_end = models.DateField(blank=True, null=True)

    Need to include a "history_key=" attribute containing the name of the model field to be used in the filter when checking for overlapping date ranges.

    Example::

      class Membership(HistoryModel):
          member = models.ForeignKey(Member)
          group = models.ForeignKey(Group)

          history_key = 'member'
          ...

    """
    date_begin = models.DateField(blank=True, null=True)
    date_end = models.DateField(blank=True, null=True)

    class Meta:
        abstract = True

    def clean(self):
        """
        Make sure self.begin_date <= self.end_date.

        Make sure self.begin_date & self.end_date don't overlap with other 'history_key' objects.
        """
        if self.date_begin and self.date_end:
            if self.date_end < self.date_begin:
                raise ValidationError("Can't have a begin date AFTER an end date")
        f = { self.history_key: getattr(self, self.history_key) }
        full_history = self.__class__._default_manager.filter(**f)
        if self.pk:
            full_history = full_history.exclude(pk=self.pk)
        if full_history.current(as_of=self.date_begin).exists() or full_history.current(as_of=self.date_end).exists():
            raise ValidationError("Can't have overlapping history dates for %s" % self)
        super(HistoryModel, self).clean()



class AddressModel(models.Model):
    street = models.CharField(max_length=255, help_text='', blank=True)
    city = models.CharField(max_length=255, default="St. Louis", blank=True)
    state = USStateField(default="MO", blank=True, null=True)
    zipcode = models.CharField(max_length=20, blank=True, null=True)

    @property
    def address(self):
        return "%s %s, %s  %s" % (self.street, self.city, self.state, self.zipcode)

    def __unicode__(self):
        return u'%s' % (self.address,)

    class Meta:
        ordering = ('street',)
        unique_together = ('street', 'zipcode')
        abstract = True


