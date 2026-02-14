class MockCelery:
    def task(self, *args, **kwargs):
        return lambda f: f
    def config_from_object(self, *args, **kwargs): pass
    def autodiscover_tasks(self, *args, **kwargs): pass
    def send_task(self, *args, **kwargs): pass
    class conf:
        @staticmethod
        def update(*args, **kwargs): pass

celery_app = MockCelery()
# Redis connection attempt blocked for Cloud Run stability.
