#!/usr/bin/env python3
"""Update version numbers across the project."""
import json
from pathlib import Path

def read_version():
    """Read version from VERSION file."""
    version_file = Path(__file__).parent.parent / 'VERSION'
    with open(version_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

def update_manifest():
    """Update version in manifest.json."""
    manifest_file = Path(__file__).parent.parent / 'custom_components' / 'remote_assist_display' / 'manifest.json'
    with open(manifest_file, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    manifest['version'] = read_version()
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')  # Add newline at end of file

def update_buildozer_spec():
    """Update version in buildozer.spec."""
    spec_file = Path(__file__).parent.parent / 'application' / 'build' / 'buildozer.spec'
    if not spec_file.exists():
        return
    
    version = read_version()
    
    # Read current content
    with open(spec_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update version line
    for i, line in enumerate(lines):
        if line.startswith('version ='):
            lines[i] = f'version = {version}\n'
    
    # Write back
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def update_flask_config():
    """Update version in flask_config.py."""
    config_file = Path(__file__).parent.parent / 'application' / 'remote_assist_display' / 'flask_config.py'
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    version = read_version()
    # Update version line
    for i, line in enumerate(lines):
        if line.strip().startswith('VERSION ='):
            lines[i] = f'    VERSION = "{version}"\n'
    
    # Write back
    with open(config_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def main():
    """Main entry point."""
    version = read_version()
    print(f"Updating version to: {version}")
    
    update_manifest()
    print("Updated manifest.json")
    
    update_buildozer_spec()
    print("Updated buildozer.spec")

    update_flask_config()
    print("Updated flask_config.py")

if __name__ == '__main__':
    main()
