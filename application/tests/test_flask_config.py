from remote_assist_display.flask_config import get_hostname, get_mac_address


def test_get_hostname(mock_hostname):
    """Test hostname retrieval."""
    hostname = get_hostname()
    assert hostname == "test-hostname"


def test_get_mac_address(mock_uuid_node):
    """Test MAC address formatting."""
    mac = get_mac_address()
    assert mac == "112233445566"
    assert len(mac) == 12
    int(mac, 16)  # Verify it's a valid hex string


def test_config_values(app, mock_hostname, mock_uuid_node):
    """Test that config values are set correctly."""
    assert app.config["MAC_ADDRESS"] == "112233445566"
    assert app.config["HOSTNAME"] == "test-hostname"
    assert app.config["UNIQUE_ID"] == "remote-assist-display-112233445566-test-hostname"
