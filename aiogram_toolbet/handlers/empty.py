async def pass_callback(call, *args, **kwargs):
    await call.answer(cache_time=60)
