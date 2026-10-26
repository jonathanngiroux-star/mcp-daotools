# mcp-daotools

MCP server for DAO governance tooling - proposal tracking, voting analytics, delegate statistics.

## Tools

### get_proposals
Get proposals for a DAO.

**Parameters:**
- `dao_id` (string, required): DAO identifier (e.g., "uniswap", "compound")
- `status` (string, optional): "active", "passed", "rejected", or "all" (default: "all")

### get_voting_analytics
Get voting analytics for a DAO.

**Parameters:**
- `dao_id` (string, required): DAO identifier

### get_delegate_stats
Get delegate statistics for a DAO.

**Parameters:**
- `dao_id` (string, required): DAO identifier

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Connecting to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "daotools": {
      "command": "python",
      "args": ["/path/to/mcp-daotools/main.py"],
      "cwd": "/path/to/mcp-daotools"
    }
  }
}
```

## License

MIT