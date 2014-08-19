from django.db import models
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
        return self.filter(is_published=True)

    def unpublished(self):
        return self.filter(is_published=False)

    def valid(self):
        return self.filter(is_valid=True)

    def invalid(self):
        return self.filter(is_valid=False)

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def current(self, begin_field='date_begin', end_field='date_end', as_of=None):
        """ 
        Filter for objects where as_of falls between begin_field, end_field.
        begin_field -> inclusive
        end_field -> not inclusive
        """
        #FIXME: take into account blank begin/end times
        if as_of is None:
            as_of = datetime.datetime.now()

        f = { 
            '%s__lte' % (begin_field,): as_of,
            '%s__gt' % (end_field,): as_of,
        }
        return self.filter(**f)

    def past(self, begin_field='date_begin', end_field='date_end', as_of=None):
        """ 
        Filter for objects where as_of falls on or after end_field.
        """
        #FIXME: take into account blank begin/end times
        if as_of is None:
            as_of = datetime.datetime.now()

        f = { 
            '%s__lt' % (end_field,): as_of,
        }
        return self.filter(**f)

    def future(self, begin_field='date_begin', end_field='date_end', as_of=None):
        """ 
        Filter for objects where as_of falls before begin_field.
        """
        #FIXME: take into account blank begin/end times
        if as_of is None:
            as_of = datetime.datetime.now()

        f = { 
            '%s__gt' % (begin_field,): as_of,
        }
        return self.filter(**f)
