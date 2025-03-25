#!/usr/bin/env python3
"""Update version numbers across the project."""
import json
import re
import sys
from pathlib import Path

def read_version():
    """Read version from VERSION file."""
    version_file = Path(__file__).parent.parent / 'VERSION'
    with open(version_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

def parse_version(version_str):
    """Parse version string into components and check if it's a dev version."""
    # Extract the basic version parts and any suffix
    match = re.match(r'(\d+)\.(\d+)\.(\d+)(?:-([a-z]+))?', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    suffix = match.group(4)  # Will be None if no suffix
    
    is_dev = suffix == 'dev'
    
    return {
        'major': major,
        'minor': minor, 
        'patch': patch,
        'suffix': suffix,
        'is_dev': is_dev,
        'clean_version': f"{major}.{minor}.{patch}"
    }

def generate_android_version_code(version_info):
    """Generate Android versionCode from version components."""
    # Using the format: major*100000 + minor*1000 + patch*10 + (0 for release, 1 for dev)
    return (version_info['major'] * 100000 + 
            version_info['minor'] * 1000 + 
            version_info['patch'] * 10 + 
            (1 if version_info['is_dev'] else 0))

def update_manifest(version_info):
    """Update version in manifest.json."""
    manifest_file = Path(__file__).parent.parent / 'custom_components' / 'remote_assist_display' / 'manifest.json'
    with open(manifest_file, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    version_str = f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
    if version_info['suffix']:
        version_str += f"-{version_info['suffix']}"
    
    manifest['version'] = version_str
    
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')

def update_buildozer_spec(version_info):
    """Update version in buildozer.spec."""
    spec_file = Path(__file__).parent.parent / 'application' / 'build' / 'buildozer.spec'
    if not spec_file.exists():
        return
        
    # Read current content
    with open(spec_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Full version string for versionName
    version_str = f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
    if version_info['suffix']:
        version_str += f"-{version_info['suffix']}"
    
    # Calculate versionCode
    version_code = generate_android_version_code(version_info)
    
    # Update version lines
    for i, line in enumerate(lines):
        if line.startswith('version ='):
            lines[i] = f'version = {version_str}\n'
        elif line.strip().startswith('# android.numeric_version ='):
            lines[i] = f'android.numeric_version = {version_code}\n'
    
    # Write back
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def update_flask_config(version_info):
    """Update version in flask_config.py."""
    config_file = Path(__file__).parent.parent / 'application' / 'remote_assist_display' / 'flask_config.py'
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Full version string with suffix if present
    version_str = f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
    if version_info['suffix']:
        version_str += f"-{version_info['suffix']}"
    
    # Update version line
    for i, line in enumerate(lines):
        if line.strip().startswith('VERSION ='):
            lines[i] = f'    VERSION = "{version_str}"\n'
    
    # Write back
    with open(config_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def bump_to_next_dev_version():
    """Bump the version to the next development version."""
    version_file = Path(__file__).parent.parent / 'VERSION'
    version_str = read_version()
    
    # Parse the current version
    version_info = parse_version(version_str)
    
    # If it's a dev version, do nothing
    if version_info['is_dev']:
        print("Already on a development version, no need to bump")
        return False
    
    # Bump the patch version and add -dev suffix
    new_version = f"{version_info['major']}.{version_info['minor']}.{version_info['patch'] + 1}-dev"
    
    # Write the new version
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(new_version)
    
    print(f"Bumped version from {version_str} to {new_version}")
    return True

def strip_dev_suffix():
    """Remove the -dev suffix for release."""
    version_file = Path(__file__).parent.parent / 'VERSION'
    version_str = read_version()
    
    # Parse the current version
    version_info = parse_version(version_str)
    
    # If it's not a dev version, do nothing
    if not version_info['is_dev']:
        print("Not a development version, no need to strip suffix")
        return False
    
    # Remove the dev suffix
    new_version = version_info['clean_version']
    
    # Write the new version
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(new_version)
    
    print(f"Stripped dev suffix: {version_str} → {new_version}")
    return True

def main():
    """Main entry point."""
    # Check for command arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "bump":
            if bump_to_next_dev_version():
                # Re-run the script to update all files with the new version
                main()
            return
        elif command == "release":
            if strip_dev_suffix():
                # Re-run the script to update all files with the new version
                main()
            return
    
    # Default behavior: update all files with current version
    version_str = read_version()
    version_info = parse_version(version_str)
    
    print(f"Updating version to: {version_str}")
    print(f"Android versionCode: {generate_android_version_code(version_info)}")
    
    update_manifest(version_info)
    print("Updated manifest.json")
    
    update_buildozer_spec(version_info)
    print("Updated buildozer.spec")

    update_flask_config(version_info)
    print("Updated flask_config.py")

if __name__ == '__main__':
    main()
