import asyncio
import pathlib
from fastmcp import Client
import os

async def test_readme_ai():
    
    # Setup path to the readme_ai_server.py script, relative to the current file
    current_dir = pathlib.Path(__file__).parent        
    server_path = current_dir.parent / "src" / "readme_ai_server.py"
    server_path = str(server_path.resolve())
    
    # Initialize the FastMCP client with stdio transport
    client = Client(server_path)
    
    # Set the environment variable for DATA_DIR for the test
    client.transport.env = {'DATA_DIR': str(current_dir / "data")}
    
    # Test the readme_ai tool with a sample repository URL
    repo_url = "https://github.com/usnistgov/hedgehog"
    
    async with client:
        
        # Test if the readme_ai tool is available
        tools = await client.list_tools()
        assert(tools[0].name == 'readme_ai')
        #print("Available tools:", tools)
        
        # Call the readme_ai tool with the repository URL
        result = await client.call_tool("readme_ai", {"repo_url" : repo_url })
        #print("Server response:", result)
        
        # Check if the result is not None and does not contain an error
        assert result is not None
        if isinstance(result, dict):        
            assert "error" not in result
            
    print('Test completed successfully!')
        

if __name__ == "__main__":
    asyncio.run(test_readme_ai())