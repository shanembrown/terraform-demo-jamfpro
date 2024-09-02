import os
import subprocess
import re
import sys

def get_latest_tag():
    """
    Retrieve the latest Git tag.

    Returns:
        str: The latest Git tag, or None if no tags are found.
    """
    try:
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0', '--match', 'v*'], stderr=subprocess.DEVNULL).decode().strip()
        print(f"Latest Git tag found: {tag}")
        return tag
    except subprocess.CalledProcessError:
        print("No Git tags found.")
        return None

def get_changed_files(latest_tag):
    """
    Get a list of files changed since the latest tag or all files if no tag exists.
    Handles renamed files gracefully.

    Args:
        latest_tag (str): The latest Git tag, or None if no tags exist.

    Returns:
        list: A list of changed file paths.
    """
    if latest_tag:
        try:
            # Use --diff-filter=ACMRT to include only added, copied, modified, renamed, or type-changed files
            files = subprocess.check_output(['git', 'diff', '--name-status', '--diff-filter=ACMRT', latest_tag, 'HEAD']).decode().split('\n')
            print(f"Files changed since {latest_tag}:")
            changed_files = []
            for file in files:
                if file:
                    status, *paths = file.split('\t')
                    if status.startswith('R'):  # Renamed file
                        print(f"  - Renamed: {paths[0]} -> {paths[1]}")
                        changed_files.append(paths[1])  # Add the new filename
                    else:
                        print(f"  - {paths[0]}")
                        changed_files.append(paths[0])
            return changed_files
        except subprocess.CalledProcessError:
            print("Error: Unable to get changed files. Using all files instead.")
    
    # If no tag exists or there's an error, return all tracked files
    files = subprocess.check_output(['git', 'ls-files']).decode().split('\n')
    print("No previous tag found or error occurred. Using all tracked files:")
    return [file for file in files if file]

def file_exists(file_path):
    """
    Check if a file exists.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    return os.path.isfile(file_path)

def read_file_content(file_path):
    """
    Read the content of a file with UTF-8 encoding.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file, or an empty string if the file doesn't exist.

    Raises:
        UnicodeDecodeError: If the file cannot be decoded using UTF-8.
    """
    if not file_exists(file_path):
        print(f"Warning: File {file_path} does not exist. Skipping.")
        return ""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        print(f"Successfully read content from {file_path}")
        return content
    except UnicodeDecodeError:
        print(f"Error: Unable to decode file {file_path} with UTF-8 encoding.")
        return ""
    except IOError as e:
        print(f"Error: Unable to read file {file_path}. {str(e)}")
        return ""

def parse_resource(content):
    """
    Parse Terraform resource blocks from the given content.

    Args:
        content (str): The content of a Terraform file.

    Returns:
        dict: A dictionary of resources, their types, names, and fields.
    """
    resources = {}
    current_resource = None
    for line in content.split('\n'):
        resource_match = re.match(r'resource\s+"(\w+)"\s+"(\w+)"\s*{', line)
        if resource_match:
            current_resource = (resource_match.group(1), resource_match.group(2))
            resources[current_resource] = {}
            print(f"Found resource: {current_resource[0]} '{current_resource[1]}'")
        elif current_resource and '=' in line:
            field, value = map(str.strip, line.split('=', 1))
            resources[current_resource][field] = value.rstrip(',')
            print(f"  Field: {field} = {value.rstrip(',')}")
        elif line.strip() == '}':
            current_resource = None
    return resources

def is_new_resource_type(changed_files, config_directory):
    """
    Check if any new resource type is introduced in the changed files.

    Args:
        changed_files (list): List of changed file paths.
        config_directory (str): The directory containing Terraform configurations.

    Returns:
        bool: True if a new resource type is found, False otherwise.
    """
    existing_resources = set()
    new_resources = set()

    print("Checking for new resource types:")
    for root, _, files in os.walk(config_directory):
        for file in files:
            if file.endswith('.tf'):
                content = read_file_content(os.path.join(root, file))
                resources = parse_resource(content)
                existing_resources.update(resource[0] for resource in resources)
    print(f"Existing resource types: {', '.join(existing_resources)}")

    for file in changed_files:
        if file.endswith('.tf') and file.startswith(config_directory):
            content = read_file_content(file)
            resources = parse_resource(content)
            new_resources.update(resource[0] for resource in resources)
    print(f"Resource types in changed files: {', '.join(new_resources)}")

    new_resource_types = new_resources - existing_resources
    if new_resource_types:
        print(f"New resource type(s) found: {', '.join(new_resource_types)}")
        return True
    else:
        print("No new resource types found.")
        return False

def is_new_resource_iteration(changed_files, config_directory):
    """
    Check if a new iteration of an existing resource type is introduced.

    Args:
        changed_files (list): List of changed file paths.
        config_directory (str): The directory containing Terraform configurations.

    Returns:
        bool: True if a new iteration is found, False otherwise.
    """
    existing_resources = {}
    new_resources = {}

    print("Checking for new resource iterations:")
    for root, _, files in os.walk(config_directory):
        for file in files:
            if file.endswith('.tf'):
                content = read_file_content(os.path.join(root, file))
                for (resource_type, resource_name), _ in parse_resource(content).items():
                    existing_resources.setdefault(resource_type, set()).add(resource_name)
    print("Existing resources:")
    for resource_type, names in existing_resources.items():
        print(f"  {resource_type}: {', '.join(names)}")

    for file in changed_files:
        if file.endswith('.tf') and file.startswith(config_directory):
            content = read_file_content(file)
            for (resource_type, resource_name), _ in parse_resource(content).items():
                new_resources.setdefault(resource_type, set()).add(resource_name)
    print("Resources in changed files:")
    for resource_type, names in new_resources.items():
        print(f"  {resource_type}: {', '.join(names)}")

    for resource_type, new_names in new_resources.items():
        if resource_type in existing_resources:
            new_iterations = new_names - existing_resources[resource_type]
            if new_iterations:
                print(f"New iteration(s) found for {resource_type}: {', '.join(new_iterations)}")
                return True

    print("No new resource iterations found.")
    return False

def is_field_changed(changed_files, config_directory):
    """
    Check if any fields have been added or removed from existing resources.

    Args:
        changed_files (list): List of changed file paths.
        config_directory (str): The directory containing Terraform configurations.

    Returns:
        bool: True if fields have changed, False otherwise.
    """
    existing_resources = {}
    new_resources = {}

    print("Checking for field changes in existing resources:")
    for root, _, files in os.walk(config_directory):
        for file in files:
            if file.endswith('.tf'):
                content = read_file_content(os.path.join(root, file))
                existing_resources.update(parse_resource(content))
    print("Existing resource fields:")
    for resource, fields in existing_resources.items():
        print(f"  {resource[0]} '{resource[1]}': {', '.join(fields.keys())}")

    for file in changed_files:
        if file.endswith('.tf') and file.startswith(config_directory):
            content = read_file_content(file)
            new_resources.update(parse_resource(content))
    print("Resource fields in changed files:")
    for resource, fields in new_resources.items():
        print(f"  {resource[0]} '{resource[1]}': {', '.join(fields.keys())}")

    for resource, new_fields in new_resources.items():
        if resource in existing_resources:
            if set(new_fields.keys()) != set(existing_resources[resource].keys()):
                added = set(new_fields.keys()) - set(existing_resources[resource].keys())
                removed = set(existing_resources[resource].keys()) - set(new_fields.keys())
                print(f"Fields changed for {resource[0]} '{resource[1]}':")
                if added:
                    print(f"  Added: {', '.join(added)}")
                if removed:
                    print(f"  Removed: {', '.join(removed)}")
                return True

    print("No field changes found in existing resources.")
    return False

def is_field_value_changed(changed_files, config_directory):
    """
    Check if any field values have changed in existing resources.

    Args:
        changed_files (list): List of changed file paths.
        config_directory (str): The directory containing Terraform configurations.

    Returns:
        bool: True if field values have changed, False otherwise.
    """
    existing_resources = {}
    new_resources = {}

    print("Checking for field value changes in existing resources:")
    for root, _, files in os.walk(config_directory):
        for file in files:
            if file.endswith('.tf'):
                content = read_file_content(os.path.join(root, file))
                existing_resources.update(parse_resource(content))
    print("Existing resource field values:")
    for resource, fields in existing_resources.items():
        print(f"  {resource[0]} '{resource[1]}':")
        for field, value in fields.items():
            print(f"    {field} = {value}")

    for file in changed_files:
        if file.endswith('.tf') and file.startswith(config_directory):
            content = read_file_content(file)
            new_resources.update(parse_resource(content))
    print("Resource field values in changed files:")
    for resource, fields in new_resources.items():
        print(f"  {resource[0]} '{resource[1]}':")
        for field, value in fields.items():
            print(f"    {field} = {value}")

    for resource, new_fields in new_resources.items():
        if resource in existing_resources:
            for field, value in new_fields.items():
                if field in existing_resources[resource] and value != existing_resources[resource][field]:
                    print(f"Field value changed for {resource[0]} '{resource[1]}':")
                    print(f"  {field}: '{existing_resources[resource][field]}' -> '{value}'")
                    return True

    print("No field value changes found in existing resources.")
    return False

def determine_version_increment(config_directory):
    latest_tag = get_latest_tag()
    changed_files = get_changed_files(latest_tag)

    if not latest_tag:
        print("No existing tags found. Treating as initial major version.")
        return 'major'

    print("\nEvaluating changes for version increment:")
    
    changes = {
        'major': False,
        'minor': False,
        'patch': False
    }

    if is_new_resource_type(changed_files, config_directory):
        changes['major'] = True
    if is_new_resource_iteration(changed_files, config_directory):
        changes['minor'] = True
    if is_file_added_or_renamed(changed_files, config_directory):
        changes['minor'] = True
    if is_resource_removed_or_commented(changed_files, config_directory):
        changes['minor'] = True
    if is_field_changed(changed_files, config_directory):
        changes['patch'] = True
    if is_field_value_changed(changed_files, config_directory):
        changes['patch'] = True
        
    if changes['major']:
        print("Major version increment: Significant changes detected.")
        return 'major'
    elif changes['minor']:
        print("Minor version increment: Notable changes detected.")
        return 'minor'
    elif changes['patch']:
        print("Patch version increment: Small changes detected.")
        return 'patch'
    else:
        print("No changes detected. Defaulting to patch increment.")
        return 'patch'

def is_file_added_or_renamed(changed_files, config_directory):
    print("Checking for added or renamed files:")
    for file in changed_files:
        if file.endswith('.tf') and file.startswith(config_directory):
            print(f"  New or renamed file detected: {file}")
            return True
    print("No new or renamed files detected.")
    return False

def is_resource_removed_or_commented(changed_files, config_directory):
    print("Checking for removed or commented resources:")
    for file in changed_files:
        if file.endswith('.tf') and file.startswith(config_directory):
            old_content = subprocess.check_output(['git', 'show', f'HEAD:{file}'], stderr=subprocess.DEVNULL).decode()
            new_content = read_file_content(file)
            old_resources = set(parse_resource(old_content).keys())
            new_resources = set(parse_resource(new_content).keys())
            removed_resources = old_resources - new_resources
            if removed_resources:
                print(f"  Removed or commented resources in {file}: {', '.join(map(str, removed_resources))}")
                return True
    print("No removed or commented resources detected.")
    return False

def set_output(name, value):
    """
    Set a GitHub Actions output variable.

    Args:
        name (str): The name of the output variable.
        value (str): The value to set.
    """
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as fh:
        print(f'{name}={value}', file=fh)
    print(f"GitHub Actions output set: {name}={value}")

def set_env(name, value):
    """
    Set a GitHub Actions environment variable.

    Args:
        name (str): The name of the environment variable.
        value (str): The value to set.
    """
    with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as fh:
        print(f'{name}={value}', file=fh)
    print(f"GitHub Actions environment variable set: {name}={value}")

def main():
    """
    Main function to determine and set the new version based on Terraform changes.

    Usage:
        python version_determinator.py <config_directory>

    Args:
        config_directory (str): The directory containing Terraform configurations.

    Exits:
        0: Success
        1: Incorrect number of arguments or invalid directory
    """
    if len(sys.argv) != 2:
        print("Usage: python version_determinator.py <config_directory>", file=sys.stderr)
        sys.exit(1)

    config_directory = sys.argv[1]
    if not os.path.isdir(config_directory):
        print(f"Error: {config_directory} is not a valid directory", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing Terraform configurations in: {config_directory}")
    increment_type = determine_version_increment(config_directory)

    latest_tag = get_latest_tag()
    if latest_tag:
        version_match = re.match(r'v(\d+)\.(\d+)\.(\d+)', latest_tag)
        if version_match:
            major, minor, patch = map(int, version_match.groups())
            print(f"Current version: v{major}.{minor}.{patch}")
        else:
            print(f"Warning: Latest tag {latest_tag} does not match expected format. Starting from 0.0.0.")
            major, minor, patch = 0, 0, 0
    else:
        print("No existing tags found. Starting from version 0.0.0.")
        major, minor, patch = 0, 0, 0

    if increment_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif increment_type == 'minor':
        minor += 1
        patch = 0
    else:
        patch += 1

    new_version = f"v{major}.{minor}.{patch}"
    
    # Set GitHub Actions output
    set_output('version', new_version)
    
    # Set environment variable
    set_env('NEW_VERSION', new_version)
    
    # Print to stdout for logging purposes
    print(f"New version determined: {new_version}")

if __name__ == "__main__":
    main()