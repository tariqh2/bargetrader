class StagingRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'trading':
            return 'staging'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'trading':
            return 'staging'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'trading' or obj2._meta.app_label == 'trading':
            return True
        # Allow relations if one of the objects is 'auth' model (User)
        if 'auth' in [obj1._meta.app_label, obj2._meta.app_label]:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'trading':
            return db == 'staging'
        return None
