import importlib
import pkgutil

import app.handlers
from app.handlers.base import BaseJobHandler


class JobHandlerFactory:
    _handlers: dict[str, BaseJobHandler] = {}

    @classmethod
    def _load_handlers(cls):
        if cls._handlers:
            return

        for _, module_name, _ in pkgutil.iter_modules(app.handlers.__path__):
            if module_name in {"base", "factory", "__init__"}:
                continue

            module = importlib.import_module(f"app.handlers.{module_name}")

            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseJobHandler)
                    and attr is not BaseJobHandler
                ):
                    instance = attr()
                    cls._handlers[instance.job_type] = instance

    @classmethod
    def get_handler(cls, job_type: str):
        cls._load_handlers()

        normalized_job_type = job_type.strip().lower()
        handler = cls._handlers.get(normalized_job_type)

        if not handler:
            raise ValueError(f"Unsupported job type: {job_type}")

        return handler