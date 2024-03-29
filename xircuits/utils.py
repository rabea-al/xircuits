import os
import urllib
import urllib.parse
import pkg_resources
import shutil

def is_empty(directory):
    # will return true for uninitialized submodules
    return not os.path.exists(directory) or not os.listdir(directory)

def is_valid_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    
def copy_from_installed_wheel(package_name, resource="", dest_path=None, add_missing_files=False):
    if dest_path is None:
        dest_path = package_name

    resource_path = pkg_resources.resource_filename(package_name, resource)
    
    if add_missing_files:
        if os.path.exists(dest_path):
            for src_dir, _, files in os.walk(resource_path):
                dst_dir = os.path.join(dest_path, os.path.relpath(src_dir, resource_path))
                os.makedirs(dst_dir, exist_ok=True)
                for file in files:
                    src_file = os.path.join(src_dir, file)
                    dst_file = os.path.join(dst_dir, file)
                    # Only copy the file if it does not exist in the destination
                    if not os.path.exists(dst_file):
                        shutil.copy(src_file, dst_file)
        else:
            # If the destination path does not exist, copy the entire tree
            shutil.copytree(resource_path, dest_path)
    else:
        # Copy the entire directory if not doing selective copying
        shutil.copytree(resource_path, dest_path, dirs_exist_ok=True)