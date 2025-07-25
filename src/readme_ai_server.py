import os
import json
import shutil
from git import Repo
import pathlib
from utils import fetch, download, crawl
from fastmcp import FastMCP

mcp = FastMCP("FastMCP Server")

@mcp.tool
async def readme_ai(repo_url: str) -> dict:
    """
    The function is designed to generate comprehensive context about a specified data source repository. This context is crucial for enhancing the LLM's understanding and ability to provide accurate and relevant information related to the data source.
    Input Parameters:
        - URL or Library Name: The function accepts either the URL of a data source repository or its library name as input. This input serves as the identifier for the data source about which context is to be generated.
        - If the user input is a library name, the function will look up the corresponding repository URL from a pre-defined mapping stored in a 'lookup.json' file.
    Functionality:
    Upon receiving the input (URL or library name), the repository will be cloned or pulled for updates, and the Readme_AI.json file will be accessed
    The function leverages pre-created context by the data source owner to build a rich understanding of the data source. 
    The context includes:
        - Files of Interest: Specific files within the data source repository that are deemed important or relevant by the owner. This could include data dictionaries, primary datasets, or example scripts.
        - Examples of Use: Practical examples or tutorials on how to utilize the data source effectively. This might encompass code snippets in various programming languages or detailed walkthroughs.
        - Related Publications: Research papers, articles, or other publications that are associated with the data source. These could provide deeper insights into the data's origin, methodology, or findings.
        - Crawled Documentation and Related Web-sites: Relevant online documentation or websites that have been crawled and indexed for quick reference. This might include official documentation, FAQs, or community forums.
        - Structured Input: Organized information about the data source, including descriptions and usage guidelines. This structured data is designed to facilitate easy comprehension and application of the data source.
    Examples:
    To illustrate the function's utility, consider the following examples:
    Input: The URL or library name of a GitHub repository for the NIST developed Hedgehog library.
        - Context Generated: The function might provide information on the specific API files within the repository, examples of how to use the library for parallel computations, links to relevant research papers that have utilized the library, and a structured summary of the library's features and usage instructions.
    Purpose and Benefits:
    The primary purpose of this function is to equip the LLM with a deeper understanding of various data sources, thereby enhancing its capability to provide informed responses, suggest relevant analyses, or guide users in effectively utilizing the data. By providing comprehensive context, the function aids in:
        - Improving the accuracy of the LLM's responses related to the data source.
        - Facilitating the discovery of relevant data and resources.
        - Assisting users in understanding how to apply the data source to their specific needs or research questions.
    """

    if 'DATA_DIR' not in os.environ:
        os.environ["DATA_DIR"] = "./data"

    data_dir = os.environ["DATA_DIR"]
    print(f"Data directory: {data_dir}")

    if "http" not in repo_url and "https" not in repo_url:
        lookup_path = str(next(pathlib.Path(data_dir).rglob("lookup.json")))
        if os.path.exists(lookup_path):
            with open(lookup_path, "r") as f:
                lookup = json.load(f)
            for key, value in lookup.items():
                if key in repo_url:
                    repo_url = value
                    break

    # Extract GitHub URL using regex
    import re
    match = re.search(r'https?://\S+', repo_url).group(0)

    if match:
        repo_url = match
    else:
        return {"error": "Invalid GitHub repository URL"}
    
    # Parse the repo URL
    url_parts = repo_url.replace("http://", "").replace("https://", "").split("/")
    
    # Remove .git from the last part if present
    repo_name = url_parts[-1].replace(".git", "")
    url_parts[-1] = repo_name

    # Create directories and subdirectories based on the URL parts
    path = os.path.join(data_dir, "data") 
    
    if not os.path.exists(path):
        os.makedirs(path)
    for part in url_parts:
        path = os.path.join(path, part)
        if not os.path.exists(path):
            os.makedirs(path)

    # The repo directory is where we'll clone/pull the repo
    repo_path = os.path.join(path, "repo")
    print(f"Repo path: {repo_path}")
    
    repo_url_with_git = repo_url if repo_url.endswith(".git") else repo_url + ".git"
    
    if os.path.exists(repo_path) and os.path.exists(os.path.join(repo_path, ".git")):
        # Pull the repo if it already exists
        try:
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            origin.pull()
            print(f"Pulled {repo_url} into {repo_path}")
        except Exception as e:
            print(f"Failed to pull {repo_url}: {e}")
            return {"error": f"Failed to pull {repo_url}: {e}"}
    else:
        # Remove existing directory if it's not a git repo
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        
        # Clone the repo if it doesn't exist or is not a git repo
        try:
            Repo.clone_from(repo_url_with_git, repo_path)
            print(f"Cloned {repo_url} into {repo_path}")
        except Exception as e:
            print(f"Failed to clone {repo_url}: {e}")
            return {"error": f"Failed to clone {repo_url}: {e}"}
    
    # Update the 'lookup.json' file
    lookup_path = os.path.join(repo_path, "lookup.json")
    if os.path.exists(lookup_path) and os.path.getsize(lookup_path) > 0:
        with open(lookup_path, "r") as f:
            try:
                lookup_dict = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing 'lookup.json': {e}")
                lookup_dict = {}
    else:
        lookup_dict = {}

    lookup_dict[repo_name] = repo_url
    with open(lookup_path, "w") as f:
        json.dump(lookup_dict, f, indent=4)

    # Load existing Readme_AI.json into a dictionary
    ai_readme_path = os.path.join(repo_path, "Readme_AI.json")
    i = 1

    if os.path.exists(ai_readme_path):
        with open(ai_readme_path, "r", encoding="utf-8") as f:
            ai_readme = json.load(f)
            text = ""
            for key, value in ai_readme.items():
                if isinstance(value, dict):
                    # Handle nested dictionary
                    nested_text = ""
                    type = value.get("type")
                    
                    if type is not None:
                        if "crawl" in type:
                            nested_text = crawl(value.get("data"))
                        elif "fetch" in type:
                            print(f"Fetching data")
                            for filepath, description in value.get('data').items():
                                nested_text += f"\n<DESCRIPTION>\n{description}\n<\DESCRIPTION>\n" + fetch(filepath, repo_path, i)
                                i += 1
                        elif "download" in type:
                            nested_text = download(value.get("data"))
                        elif "files" in type:
                            for file in value.get("data"):
                                if ".pdf" in file:
                                    nested_text += download([file])
                                elif ".txt" in file:
                                    with open(file, "r") as f:
                                        nested_text += f.read() + "\n"
                        elif "text" in type:
                            nested_text = value.get('data')
                    else:
                        # If 'type' is not present, iterate through key-value pairs
                        for nested_key, nested_value in value.items():
                            nested_text += f"\n<{nested_key.upper()}>\n{nested_value}\n<\{nested_key.upper()}>\n"
                    
                    text += f"\n\n<{key.upper()}>\n{nested_text}\n</{key.upper()}>\n\n"
                else:
                    text += f"\n\n<{key.upper()}>\n{value}\n</{key.upper()}>\n\n"

        results_file_path = os.path.join(os.environ['DATA_DIR'], "results.txt")
        with open(results_file_path, "w", encoding="utf-8") as f:
            f.write(str(text))
        return text
    else:
        return {"error": "Readme_AI.json not found"}
    
if __name__ == "__main__":
    mcp.run()