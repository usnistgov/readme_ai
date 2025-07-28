import asyncio
import pathlib
from fastmcp import Client
import os

async def test_readme_ai():
    
    current_dir = pathlib.Path(__file__).parent    
    
    server_path = current_dir.parent / "src" / "readme_ai_server.py"
    server_path = str(server_path.resolve())
    print("Server path:", server_path)
    client = Client(server_path)
    
    client.transport.env = {'DATA_DIR': str(current_dir / "data")}
    
    repo_url = "https://github.com/usnistgov/hedgehog"
    
    async with client:    
        tools = await client.list_tools()
        assert(tools[0].name == 'readme_ai')
        #print("Available tools:", tools)
        result = await client.call_tool("readme_ai", {"repo_url" : repo_url })
        #print("Server response:", result)
        
        assert result is not None
        if isinstance(result, dict):        
            assert "error" not in result
            
    print('Test completed successfully!')
        

if __name__ == "__main__":
    asyncio.run(test_readme_ai())