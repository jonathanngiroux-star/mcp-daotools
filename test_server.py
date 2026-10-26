import pytest
import asyncio
import json
import secrets
from mcp_daotools.server import (
    create_dao, 
    create_proposal, 
    get_proposals,
    get_voting_analytics,
    get_delegate_stats,
    get_quorum_health,
    list_daos,
    list_tools_handler,
    call_tool_handler
)

@pytest.fixture
async def clean_db():
    import sqlite3
    from mcp_daotools.server import DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM daos")
        conn.execute("DELETE FROM proposals")
    yield
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM daos")
        conn.execute("DELETE FROM proposals")

@pytest.mark.asyncio
async def test_list_tools():
    from mcp_daotools.server import list_tools_handler
    from mcp.types import ListToolsResult
    result = await list_tools_handler()
    assert isinstance(result, ListToolsResult)
    assert len(result.tools) == 7

@pytest.mark.asyncio
async def test_create_dao(clean_db):
    from mcp_daotools.server import create_dao
    dao = await create_dao({
        "name": "Test DAO",
        "description": "Test DAO description",
        "token": "TEST",
        "governance_contract": "0x123...",
        "chain": "ethereum"
    })
    assert len(dao) > 0
    data = json.loads(dao[0].text)
    assert data["status"] == "created"
    assert "dao_id" in data

@pytest.mark.asyncio
async def test_create_proposal(clean_db):
    from mcp_daotools.server import create_dao, create_proposal
    dao = await create_dao({"name": "Test DAO", "description": "Desc", "token": "TEST", "governance_contract": "0x123", "chain": "ethereum"})
    dao_id = json.loads(dao[0].text)["dao_id"]
    
    prop = await create_proposal({
        "dao_id": dao_id,
        "title": "Test Proposal",
        "description": "Description",
        "proposer": "0xabc",
        "voting_ends_at": "2024-12-31T23:59:59"
    })
    assert len(prop) > 0
    data = json.loads(prop[0].text)
    assert data["status"] == "draft"
    assert "proposal_id" in data

@pytest.mark.asyncio
async def test_get_proposals(clean_db):
    from mcp_daotools.server import create_dao, create_proposal, get_proposals
    dao = await create_dao({"name": "Test", "description": "Desc", "token": "TEST", "governance_contract": "0x123", "chain": "ethereum"})
    dao_id = json.loads(dao[0].text)["dao_id"]
    await create_proposal({"dao_id": dao_id, "title": "Prop 1", "description": "Desc", "proposer": "0x1", "voting_ends_at": "2024-12-31T23:59:59"})
    import time
    time.sleep(0.01)
    await create_proposal({"dao_id": dao_id, "title": "Prop 2", "description": "Desc", "proposer": "0x2", "voting_ends_at": "2024-12-31T23:59:59"})
    props = await get_proposals({"dao_id": dao_id})
    data = json.loads(props[0].text)
    assert len(data["proposals"]) >= 2

@pytest.mark.asyncio
async def test_get_voting_analytics(clean_db):
    from mcp_daotools.server import create_dao, create_proposal, get_voting_analytics
    dao = await create_dao({"name": "Test", "description": "Desc", "token": "TEST", "governance_contract": "0x123", "chain": "ethereum"})
    dao_id = json.loads(dao[0].text)["dao_id"]
    await create_proposal({"dao_id": dao_id, "title": "Prop 1", "description": "Desc", "proposer": "0x1", "voting_ends_at": "2024-12-31T23:59:59"})
    analytics = await get_voting_analytics({"dao_id": dao_id})
    data = json.loads(analytics[0].text)
    assert data["total_proposals"] >= 1
    assert "by_status" in data

@pytest.mark.asyncio
async def test_list_daos(clean_db):
    from mcp_daotools.server import create_dao, list_daos
    await create_dao({"name": "DAO 1", "description": "Desc 1", "token": "T1", "governance_contract": "0x1", "chain": "ethereum"})
    await create_dao({"name": "DAO 2", "description": "Desc 2", "token": "T2", "governance_contract": "0x2", "chain": "polygon"})
    daos = await list_daos({})
    data = json.loads(daos[0].text)
    assert len(data["daos"]) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])