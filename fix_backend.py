import os
with open(r'apps\api\app\routers\dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix fetch_real_time_news
old_tavily = '''        res = await tavily.search("latest essential top breaking news headlines india tech business sports", max_results=6)'''
new_tavily = '''        import asyncio\n        res = await asyncio.wait_for(tavily.search("latest essential top breaking news headlines india tech business sports", max_results=6), timeout=3.0)'''
content = content.replace(old_tavily, new_tavily)

# Fix _generate_ai_dashboard_payload
old_llm = '''        response = await router._execute_with_router("chat", [{"role": "user", "content": prompt}], intent="dashboard")'''
new_llm = '''        import asyncio\n        response = await asyncio.wait_for(router._execute_with_router("chat", [{"role": "user", "content": prompt}], intent="dashboard"), timeout=5.0)'''
content = content.replace(old_llm, new_llm)

with open(r'apps\api\app\routers\dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)
