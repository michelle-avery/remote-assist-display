from .state import DisplayState


async def load_card(event, expire_time=None):
    await DisplayState.get_instance().load_card(event, expire_time)


async def load_dashboard(url, local_storage=True):
    await DisplayState.get_instance().load_url(url, local_storage)
