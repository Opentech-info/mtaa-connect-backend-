def patch_django_context_copy():
    """
    Work around Django BaseContext.__copy__ incompatibility with Python 3.14.
    This keeps admin templates working without changing Django internals.
    """
    try:
        from django.template.context import BaseContext
    except Exception:
        return

    def _safe_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        if hasattr(self, "__dict__"):
            duplicate.__dict__ = self.__dict__.copy()
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _safe_copy
