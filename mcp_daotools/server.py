#!/usr/bin/env python3
"""
MCP DAO Tools Server - DAO Governance Tooling via MCP
"""

import json
import asyncio
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult

DB_PATH = Path(__file__).parent / "dao.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daos (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                token TEXT NOT NULL,
                governance_contract TEXT NOT NULL,
                chain TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                dao_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                proposer TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                voting_starts_at TEXT NOT NULL,
                voting_ends_at TEXT NOT NULL,
                votes_for INTEGER DEFAULT 0,
                votes_against INTEGER DEFAULT 0,
                votes_abstain INTEGER DEFAULT 0,
                quorum INTEGER DEFAULT 0,
                FOREIGN KEY (dao_id) REFERENCES daos (id)
            )
        """)

init_db()

TOOLS = [
    Tool(
        name="create_dao",
        description="Create a new DAO",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "DAO name"},
                "description": {"type": "string", "description": "DAO description"},
                "token": {"type": "string", "description": "Governance token symbol"},
                "governance_contract": {"type": "string", "description": "Governance contract address"},
                "chain": {"type": "string", "description": "Blockchain"}
            },
            "required": ["name", "token", "governance_contract", "chain"]
        }
    ),
    Tool(
        name="create_proposal",
        description="Create a governance proposal",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO ID"},
                "title": {"type": "string", "description": "Proposal title"},
                "description": {"type": "string", "description": "Proposal description"},
                "proposer": {"type": "string", "description": "Proposer address"},
                "voting_ends_at": {"type": "string", "description": "Voting end timestamp"}
            },
            "required": ["dao_id", "title", "description", "proposer", "voting_ends_at"]
        }
    ),
    Tool(
        name="get_proposals",
        description="Get proposals for a DAO",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO ID"},
                "status": {"type": "string", "description": "Filter by status (draft, active, passed, rejected, executed)"}
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
                "dao_id": {"type": "string", "description": "DAO ID"}
            },
            "required": ["dao_id"]
        }
    ),
    Tool(
        name="get_delegate_stats",
        description="Get delegate statistics",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO ID"}
            },
            "required": ["dao_id"]
        }
    ),
    Tool(
        name="get_quorum_health",
        description="Check quorum health for active proposals",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO ID"}
            },
            "required": ["dao_id"]
        }
    ),
    Tool(
        name="list_daos",
        description="List all DAOs",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
]

async def list_tools_handler():
    from mcp.types import ListToolsResult
    return ListToolsResult(tools=TOOLS)

async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        if name == "create_dao":
            result = await create_dao(arguments)
        elif name == "create_proposal":
            result = await create_proposal(arguments)
        elif name == "get_proposals":
            result = await get_proposals(arguments)
        elif name == "get_voting_analytics":
            result = await get_voting_analytics(arguments)
        elif name == "get_delegate_stats":
            result = await get_delegate_stats(arguments)
        elif name == "get_quorum_health":
            result = await get_quorum_health(arguments)
        elif name == "list_daos":
            result = await list_daos(arguments)
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)
        return CallToolResult(content=result)
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")], isError=True)

async def create_dao(args: Dict[str, Any]) -> List[TextContent]:
    dao_id = f"dao-{args['name'].lower().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}"
    now = datetime.now().isoformat()
    dao = {
        "id": dao_id,
        "name": args["name"],
        "description": args.get("description", ""),
        "token": args["token"],
        "governance_contract": args["governance_contract"],
        "chain": args["chain"],
        "created_at": now
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO daos (id, name, description, token, governance_contract, chain, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (dao["id"], dao["name"], dao["description"], dao["token"],
              dao["governance_contract"], dao["chain"], dao["created_at"]))
    return [TextContent(type="text", text=json.dumps({"dao_id": dao_id, "status": "created"}, indent=2))]

async def create_proposal(args: Dict[str, Any]) -> List[TextContent]:
    prop_id = f"prop-{args['dao_id']}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    now = datetime.now().isoformat()
    proposal = {
        "id": prop_id,
        "dao_id": args["dao_id"],
        "title": args["title"],
        "description": args["description"],
        "proposer": args["proposer"],
        "status": "draft",
        "created_at": now,
        "voting_starts_at": now,
        "voting_ends_at": args["voting_ends_at"]
    }
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO proposals (id, dao_id, title, description, proposer, status, created_at, voting_starts_at, voting_ends_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (proposal["id"], proposal["dao_id"], proposal["title"], proposal["description"],
              proposal["proposer"], proposal["status"], proposal["created_at"],
              proposal["voting_starts_at"], proposal["voting_ends_at"]))
    return [TextContent(type="text", text=json.dumps({"proposal_id": prop_id, "status": "draft"}, indent=2))]

async def get_proposals(args: Dict[str, Any]) -> List[TextContent]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM proposals WHERE dao_id = ?"
        params = [args["dao_id"]]
        if args.get("status"):
            query += " AND status = ?"
            params.append(args["status"])
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
        proposals = [dict(r) for r in rows]
    return [TextContent(type="text", text=json.dumps({"proposals": proposals}, indent=2))]

async def get_voting_analytics(args: Dict[str, Any]) -> List[TextContent]:
    dao_id = args["dao_id"]
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) FROM proposals WHERE dao_id = ?", (dao_id,)).fetchone()[0]
        by_status = conn.execute("SELECT status, COUNT(*) FROM proposals WHERE dao_id = ? GROUP BY status", (dao_id,)).fetchall()
        total_votes = conn.execute("SELECT SUM(votes_for + votes_against + votes_abstain) FROM proposals WHERE dao_id = ?", (dao_id,)).fetchone()[0] or 0
        turnout = conn.execute("SELECT AVG((votes_for + votes_against + votes_abstain) * 1.0 / quorum) FROM proposals WHERE dao_id = ? AND quorum > 0", (dao_id,)).fetchone()[0] or 0
    return [TextContent(type="text", text=json.dumps({
        "dao_id": dao_id,
        "total_proposals": total,
        "by_status": dict(by_status),
        "total_votes_cast": total_votes,
        "avg_turnout": round(turnout * 100, 2)
    }, indent=2))]

async def get_delegate_stats(args: Dict[str, Any]) -> List[TextContent]:
    dao_id = args["dao_id"]
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT proposer, COUNT(*) as count FROM proposals WHERE dao_id = ? GROUP BY proposer ORDER BY count DESC LIMIT 10", (dao_id,)).fetchall()
        delegates = [dict(r) for r in rows]
    return [TextContent(type="text", text=json.dumps({"dao_id": dao_id, "top_delegates": delegates}, indent=2))]

async def get_quorum_health(args: Dict[str, Any]) -> List[TextContent]:
    dao_id = args["dao_id"]
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, title, quorum, votes_for + votes_against + votes_abstain as total_votes, voting_ends_at FROM proposals WHERE dao_id = ? AND status = 'active'", (dao_id,)).fetchall()
        active = [dict(r) for r in rows]
    for p in active:
        p["quorum_met"] = p["total_votes"] >= p["quorum"]
        p["quorum_pct"] = round(p["total_votes"] / p["quorum"] * 100, 1) if p["quorum"] > 0 else 0
    return [TextContent(type="text", text=json.dumps({"dao_id": dao_id, "active_proposals": active}, indent=2))]

async def list_daos(args: Dict[str, Any]) -> List[TextContent]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM daos ORDER BY created_at DESC").fetchall()
        daos = [dict(r) for r in rows]
    return [TextContent(type="text", text=json.dumps({"daos": daos}, indent=2))]

from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult

init_db()

TOOLS = [
    Tool(
        name="create_dao",
        description="Create a new DAO",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "DAO name"},
                "description": {"type": "string", "description": "DAO description"},
                "token": {"type": "string", "description": "Governance token symbol"},
                "governance_contract": {"type": "string", "description": "Governance contract address"},
                "chain": {"type": "string", "description": "Blockchain"}
            },
            "required": ["name", "token", "governance_contract", "chain"]
        }
    ),
    Tool(
        name="create_proposal",
        description="Create a governance proposal",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO ID"},
                "title": {"type": "string", "description": "Proposal title"},
                "description": {"type": "string", "description": "Proposal description"},
                "proposer": {"type": "string", "description": "Proposer address"},
                "voting_ends_at": {"type": "string", "description": "Voting end timestamp"}
            },
            "required": ["dao_id", "title", "description", "proposer", "voting_ends_at"]
        }
    ),
    Tool(
        name="get_proposals",
        description="Get proposals for a DAO",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO ID"},
                "status": {"type": "string", "description": "Filter by status"}
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
                "dao_id": {"type": "string", "description": "DAO ID"}
            },
            "required": ["dao_id"]
        }
    ),
    Tool(
        name="get_delegate_stats",
        description="Get delegate statistics",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO ID"}
            },
            "required": ["dao_id"]
        }
    ),
    Tool(
        name="get_quorum_health",
        description="Check quorum health for active proposals",
        inputSchema={
            "type": "object",
            "properties": {
                "dao_id": {"type": "string", "description": "DAO ID"}
            },
            "required": ["dao_id"]
        }
    ),
    Tool(
        name="list_daos",
        description="List all DAOs",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
]

async def list_tools_handler():
    from mcp.types import ListToolsResult
    return ListToolsResult(tools=TOOLS)

async def call_tool_handler(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    try:
        if name == "create_dao":
            result = await create_dao(arguments)
        elif name == "create_proposal":
            result = await create_proposal(arguments)
        elif name == "get_proposals":
            result = await get_proposals(arguments)
        elif name == "get_voting_analytics":
            result = await get_voting_analytics(arguments)
        elif name == "get_delegate_stats":
            result = await get_delegate_stats(arguments)
        elif name == "get_quorum_health":
            result = await get_quorum_health(arguments)
        elif name == "list_daos":
            result = await list_daos(arguments)
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")], isError=True)
        return CallToolResult(content=result)
    except Exception as e:
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")], isError=True)

app = Server(
    name="mcp-daotools",
    on_list_tools=lambda: list_tools_handler(),
    on_call_tool=lambda name, arguments: call_tool_handler(name, arguments)
)

if __name__ == "__main__":
    from mcp.server.stdio import stdio_server
    async def serve():
        server = await stdio_server()
        await app.run(server.stdin, server.stdout)
    asyncio.run(serve())