"""Use the official MCP SDK and stdio protocol; record tool schemas and results."""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = Path('E:/anaconda3/envs/llm/Scripts/blender-mcp.exe')

async def main():
    params = StdioServerParameters(command=str(SERVER), args=[], env={
        **os.environ, 'BLENDER_MCP_HOST':'127.0.0.1', 'BLENDER_MCP_PORT':'9876',
        'BLENDER_PATH':'E:/Blender/blender.exe', 'PYTHONIOENCODING':'utf-8',
        'TEMP':'E:/codex/cache/tmp', 'TMP':'E:/codex/cache/tmp',
    })
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=600)) as session:
            init = await session.initialize()
            if sys.argv[1] == 'list':
                result = await session.list_tools()
                (ROOT/'docs'/'mcp_tools.json').write_text(result.model_dump_json(indent=2), encoding='utf-8')
                print(json.dumps({'server':init.serverInfo.model_dump(), 'tools':[t.name for t in result.tools]}, ensure_ascii=False))
            else:
                tool = sys.argv[1]
                if tool == 'execute_blender_code' and len(sys.argv)>2 and sys.argv[2].endswith('.py'):
                    args = {'code':Path(sys.argv[2]).read_text(encoding='utf-8')}
                else:
                    raw=sys.argv[2] if len(sys.argv)>2 else '{}'
                    if raw.startswith('@'): raw=Path(raw[1:]).read_text(encoding='utf-8')
                    args=json.loads(raw)
                result = await session.call_tool(tool, args)
                (ROOT/'reports'/'last_mcp_result.json').write_text(result.model_dump_json(indent=2),encoding='utf-8')
                for c in result.content:
                    if c.type == 'text':
                        print(c.text)
                        try:
                            payload=json.loads(c.text)
                            if payload.get('status')=='error': raise SystemExit(1)
                        except json.JSONDecodeError: pass
                if result.isError: raise SystemExit(1)

if __name__ == '__main__':
    asyncio.run(main())
