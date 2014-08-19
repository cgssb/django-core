import os
import uuid

def uuid_upload_to(dirname):
    """ Give an uploaded file a nice generic uuid filename """
    def func(instance, filename):
        ext = filename.split('.')[-1].lower()
        filename = "%s.%s" % (uuid.uuid4(), ext)
        return os.path.join(dirname, filename)
    return func

