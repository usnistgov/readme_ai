# readme_ai
Readme_AI is a Model Context Protocol (MCP) server using the FastMCP library that dynamically builds context for LLMs using its JSON file specification.

## Installation
Clone this repository to your local machine <br> <br>
Set up a DATA_DIR environmental variable to your desired directory for storing data

### Dependencies
1. FastMCP
2. gitpython
3. pypdf
4. beautifulsoup
5. requests

## Execution
To run the Readme_AI server, execute the following command in the project directory:
```console
$ python readme_ai_server.py
```

## Roo Code
Installing Roo Code as an extension to your code editor will allow you to interact with LLMs directly within your code editor.

### Getting Started
**Installation:** Search for "Roo Code" in your code editor's extension marketplace and install it <br>
**Configuration:** Once installed, configure Roo Code to connect to the Readme_AI server. Do this by opening the mcp_settings.json file and add the following code:

```json
"hedgehog": {
      "type": "stdio",
      "command": your python environment,
      "args": [
        "readme_ai_server.py"
      ],
      "cwd": your directory,
      "env": {
        "DATA_DIR": your directory
      },
      "disabled": false,
      "alwaysAllow": []
    }
```

