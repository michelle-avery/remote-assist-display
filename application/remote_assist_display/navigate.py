from .state import DisplayState

load_card_timer = None

async def load_card(event, expire_time=None):
    await DisplayState.get_instance().load_card(event, expire_time)


async def load_dashboard(url):
    await DisplayState.get_instance().load_url(url)

def set_local_storage():
    DisplayState.get_instance().set_local_storage()
