import os

files = [
    'app/utils/jwt.py', 
    'app/services/scheduler/worker.py', 
    'app/services/scheduler/reflection.py', 
    'app/services/ai/tools/habit_tracker.py', 
    'app/services/ai/tools/expense_tracker.py', 
    'app/services/ai/planner/models.py', 
    'app/repositories/oauth_state_repository.py'
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('from datetime import UTC, datetime, timedelta', 'from datetime import datetime, timedelta, timezone')
    content = content.replace('from datetime import UTC, datetime', 'from datetime import datetime, timezone')
    content = content.replace('UTC', 'timezone.utc')
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print("SUCCESS")
