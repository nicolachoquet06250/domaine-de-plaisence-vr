import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { readFile } from 'node:fs/promises';

// The installed MCP supports this explicit opt-out; keep project assets and
// viewport captures local instead of uploading session telemetry to Supabase.
const transport = new StdioClientTransport({ command: 'C:/Users/nicol/.local/bin/uvx.exe', args: ['--offline', 'blender-mcp'],
  env: {...process.env, BLENDER_MCP_DISABLE_TELEMETRY:'true', DISABLE_TELEMETRY:'true', MCP_DISABLE_TELEMETRY:'true'} });
const client = new Client({ name: 'estate-asset-authoring', version: '1.0.0' });
try {
  await client.connect(transport);
  const command = process.argv[2] ?? 'list';
  const result = command === 'list' ? await client.listTools() : await client.callTool({
    name: command,
    arguments: process.argv[3]?.endsWith('.py') ? {
      ...JSON.parse(await readFile(process.argv[4] ?? new URL('./blender-inspect.json', import.meta.url), 'utf8')),
      code: `exec(compile(${JSON.stringify(await readFile(process.argv[3], 'utf8'))}, ${JSON.stringify(process.argv[3])}, 'exec'), __import__('bpy').__dict__.setdefault('_estate_authoring', {}))`,
    } : process.argv[3] ? JSON.parse(await readFile(process.argv[3], 'utf8')) : {},
  }, undefined, { timeout: 240000 });
  console.log(JSON.stringify(result, null, 2));
} finally { await client.close(); }
