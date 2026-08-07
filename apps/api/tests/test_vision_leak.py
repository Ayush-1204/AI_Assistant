import pytest
import re
from unittest.mock import AsyncMock

from app.services.ai.planner.upfront_planner import UpfrontPlanner

import asyncio
from typing import Any, cast

def test_upfront_planner_strips_images():
    class DummyProvider:
        async def chat(self, messages, intent="general"):
            for msg in messages:
                if "images" in msg or "base64" in str(msg.get("content", "")):
                    raise Exception("Base64 string leaked into payload!")
            return '{"tools_needed": false, "tasks": [], "output_structure": "direct_answer"}'
            
    planner = UpfrontPlanner(cast(Any, DummyProvider()))
    context_messages = [
        {"role": "system", "content": "You are a test system"},
        {"role": "user", "content": "test prompt", "images": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="]}
    ]
    
    plan = asyncio.run(planner.generate_plan("test prompt", context_messages))
    assert plan is not None

def test_context_builder_scrubs_markdown_images():
    msg_content = "Here is an image: ![attachment](data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAAAAAAD/) and another ![image](data:image/png;base64,iVBORw0KGgo=)!"
    
    clean_content = re.sub(r"!\[.*?\]\(data:image\/[^;]+;base64,[^\)]+\)", "[Attached Image]", msg_content)
    
    assert "base64" not in clean_content
    assert clean_content == "Here is an image: [Attached Image] and another [Attached Image]!"
