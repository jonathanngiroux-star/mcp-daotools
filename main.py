#!/usr/bin/env python3
"""MCP server for daotools - DAO Governance Tooling"""

import json
import os
from datetime import datetime
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("mcp-daotools")

# Simulated DAO data
DAOS = {
    "uniswap": {
        "id": "uniswap",
        "name": "Uniswap DAO",
        "token": "UNI",
        "chain": "ethereum",
        "governance_contract": "0x1f98431c8ad98523631ae4a59f267346ea31f984",
        "proposals": [
            {"id": 1, "title": "Uniswap v4 Fee Structure", "status": "active", "votes_for": 1250000, "votes_against": 340000, "quorum": 4000000, "end_date": "2024-12-31"},
            {"id": 2, "title": "Treasury Diversification", "status": "passed", "votes_for": 2100000, "votes_against": 150000, "quorum": 4000000, "end_date": "2024-11-15"},
        ],
        "delegates": [
            {"address": "0x123...", "name": "Delegate A", "voting_power": 1500000, "participation": 0.95},
            {"address": "0x456...", "name": "Delegate B", "voting_power": 800000, "participation": 0.87},
        ]
    },
    "compound": {
        "id": "compound",
        "name": "Compound DAO",
        "token": "COMP",
        "chain": "ethereum",
        "governance_contract": "0xc00e94Cb668C3587fF677b01F3e5381f1C1C7C1E",
        "proposals": [
            {"id": 280, "title": "Market Risk Parameters Update", "status": "active", "votes_for": 850000, "votes_against": 120000, "quorum": 650000, "end_date": "2024-12-20"},
        ],
        "delegates": [
            {"address": "0x789...", "name": "Delegate C", "voting_power": 900000, "participation": 0.92},
        ]
    }
}

app = Server("mcp-daotools")

TOOLS = [
    Tool(
        name="get_proposals",
        description="Get proposals for a DAO",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO identifier"},
                "status": {"type": "string", "enum": ["active", "passed", "rejected", "all"], "default": "all", "description": "Filter by status"}
            },
            "required": ["dao_id"]
        }
    ),
    Tool(
        name="get_voting_analytics",
        description="Get voting analytics for a DAO",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO identifier"}
            },
            "required": ["dao_id"]
        }
    ),
    Tool(
        name="get_delegate_stats",
        description="Get delegate statistics for a DAO",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO identifier"}
            },
            "required": ["dao_id"]
        }
    )
]

app = Server("mcp-daotools")

@app.list_tools()
async def list_tools():
    return TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_proposals":
        dao_id = arguments.get("dao_id")
        status = arguments.get("status", "all")
        
        dao = DAOS.get(dao_id)
        if not dao:
            return [TextContent(type="text", text=json.dumps({"error": f"DAO not found: {dao_id}"}))]
        
        proposals = dao.get("proposals", [])
        if status != "all":
            proposals = [p for p in proposals if p["status"] == status]
        
        result = {
            "status": "ok",
            "tool": "get_proposals",
            "dao_id": dao_id,
            "dao_name": dao["name"],
            "count": len(proposals),
            "proposals": proposals
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_voting_analytics":
        dao_id = arguments.get("dao_id")
        
        dao = DAOS.get(dao_id)
        if not dao:
            return [TextContent(type="text", text=json.dumps({"error": f"DAO not found: {dao_id}"}))]
        
        proposals = dao.get("proposals", [])
        total = len(proposals)
        passed = len([p for p in proposals if p["status"] == "passed"])
        rejected = len([p for p in proposals if p["status"] == "rejected"])
        active = len([p for p in proposals if p["status"] == "active"])
        
        total_votes = sum(p.get("votes_for", 0) + p.get("votes_against", 0) for p in proposals)
        avg_participation = sum((p.get("votes_for", 0) + p.get("votes_against", 0)) / max(p.get("quorum", 1), 1) for p in proposals) / max(len(proposals), 1) * 100
        
        result = {
            "status": "ok",
            "tool": "get_voting_analytics",
            "dao_id": dao_id,
            "dao_name": dao["name"],
            "total_proposals": total,
            "status_breakdown": {"passed": passed, "rejected": rejected, "active": active},
            "total_votes_cast": total_votes,
            "avg_participation_rate": round(avg_participation, 2)
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_delegate_stats":
        dao_id = arguments.get("dao_id")
        
        dao = DAOS.get(dao_id)
        if not dao:
            return [TextContent(type="text", text=json.dumps({"error": f"DAO not found: {dao_id}"}))]
        
        delegates = dao.get("delegates", [])
        
        result = {
            "status": "ok",
            "tool": "get_delegate_stats",
            "dao_id": dao_id,
            "dao_name": dao["name"],
            "delegate_count": len(delegates),
            "delegates": delegates
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def serve():
        reader, writer = await stdio_server()
        await app.run(reader, writer)
    
    asyncio.run(serve())