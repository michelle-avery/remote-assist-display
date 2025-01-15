from application.remote_assist_display.state import DisplayState

load_card_timer = None

def load_card(event, expire_time=None):
    DisplayState.get_instance().load_card(event, expire_time)


def load_dashboard(url):
    DisplayState.get_instance().load_url(url)

def set_local_storage():
    DisplayState.get_instance().set_local_storage()
