from django_db_logger.models import StatusLog

class MyDBRouter(object):

    def db_for_read(self, model, **hints):
        """ reading SomeModel from otherdb """
        if model == StatusLog:
            return 'django_db_logger'
        return 'default'

    def db_for_write(self, model, **hints):
        """ writing SomeModel to otherdb """
        if model == StatusLog:
            return 'django_db_logger'
        return 'default'