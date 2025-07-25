import os
import glob

def fetch(api_path: str, repo_path: str, num: int) -> str:
    """
    Given a path to data that is stored in a specific directory
    Traverses through the given path and creates the full path to the directory that contains the files
    Traverses through all the files and reads the content of each file
    Returns the content of all files in a string in XML format
    """
    data_dir = os.environ.get("DATA_DIR", "./data")
    num_file = num

    # gets all files in the directory and its subdirectories
    api_dir = os.path.join(data_dir, repo_path, api_path)

    if '*' in api_dir:
        all_files = glob.glob(os.path.join(api_dir, "**/*"), recursive=True)
    else:
        if os.path.isfile(api_dir):
            all_files = [api_dir]
        else:
            all_files = glob.glob(os.path.join(api_dir, "*"), recursive=True)
    all_files = [file for file in all_files if os.path.isfile(file)]

    api_str = ""

    # traverses through all the files
    for file in all_files:
        try:
            # reads the content of each file
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                api_str += f"\n<file{num_file}>\n{content}</file{num_file}>\n"
        except Exception as e:
            return f"Error reading file {file}: {str(e)}"
        num_file += 1
    return api_str