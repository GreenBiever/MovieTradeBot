import inspect


class HasEventHandler:

    _HANDLER_PREFIX = 'handler__'

    @classmethod
    def get_event_handler(cls, name: str) -> callable:
        return cls.get_event_handlers()[name]

    @classmethod
    def get_event_handlers(cls) -> dict[str, callable]:
        return {
            name.replace(cls._HANDLER_PREFIX, ''): method
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
            if name.startswith(cls._HANDLER_PREFIX)
        }

    def get_instance_event_handler(self, name: str) -> callable:
        # print(self.get_instance_event_handlers())
        return self.get_instance_event_handlers()[name]

    def get_instance_event_handlers(self) -> dict[str, callable]:
        return {
            name.replace(self._HANDLER_PREFIX, ''): method
            for name, method in inspect.getmembers(self, predicate=inspect.ismethod)
            if name.startswith(self._HANDLER_PREFIX)
        }
