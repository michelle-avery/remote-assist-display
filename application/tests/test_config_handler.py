import configparser

from remote_assist_display.config_handler import get_saved_config, save_to_config

def test_get_saved_config_empty(temp_config_file):
    """Test getting config when file doesn't exist."""
    config = get_saved_config()
    assert isinstance(config, configparser.ConfigParser)
    assert len(config.sections()) == 0


def test_get_saved_config_existing(sample_config, temp_config_file):
    """Test getting config with existing data."""
    config = get_saved_config()
    assert 'TestSection' in config
    assert config['TestSection']['test_key'] == 'test_value'
    assert config['TestSection']['another_key'] == 'another_value'


def test_save_to_config_new_section(temp_config_file):
    """Test saving to a new section."""
    save_to_config('NewSection', 'new_key', 'new_value')

    config = get_saved_config()
    assert 'NewSection' in config
    assert config['NewSection']['new_key'] == 'new_value'


def test_save_to_config_existing_section(sample_config, temp_config_file):
    """Test saving to an existing section."""
    save_to_config('TestSection', 'new_key', 'new_value')

    config = get_saved_config()
    assert config['TestSection']['new_key'] == 'new_value'
    assert config['TestSection']['test_key'] == 'test_value'  # Original value should remain


def test_save_to_config_update_existing_value(sample_config, temp_config_file):
    """Test updating an existing value."""
    save_to_config('TestSection', 'test_key', 'updated_value')

    config = get_saved_config()
    assert config['TestSection']['test_key'] == 'updated_value'