import uuid
from discovery import register_server

#Todo: Make this configurable once we have proper config handling
PORT = 8123

async def initialize():
    name = get_mac_address()
    port = PORT

    await register_server(name=name, port=port)
    return True

def get_mac_address() -> str:
    """Return MAC address formatted as hex with no colons."""
    return "".join(
        # pylint: disable=consider-using-f-string
        ["{:02x}".format((uuid.getnode() >> ele) & 0xFF) for ele in range(0, 8 * 6, 8)][
            ::-1
        ]
    )
