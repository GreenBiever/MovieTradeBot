from functools import wraps
from typing import Type


def ignore_handler_exception(*exc_cls: Type[Exception]):
    def _wrapper(func: callable):
        @wraps(func)
        async def _final_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exc_cls as e:
                print(f'Exception {e} ignored')
                pass

        return _final_wrapper

    return _wrapper
