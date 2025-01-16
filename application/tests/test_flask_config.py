from remote_assist_display.flask_config import get_mac_address


def test_get_mac_address(mock_uuid_node):
    """Test MAC address formatting."""
    mac = get_mac_address()
    assert mac == "112233445566"
    assert len(mac) == 12
    int(mac, 16)  # Verify it's a valid hex string