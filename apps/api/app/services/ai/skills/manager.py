import logging
import os

import aiohttp

logger = logging.getLogger(__name__)

class SkillManager:
    def __init__(self, registry):
        self.registry = registry
        ai_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.dynamic_dir = os.path.join(ai_dir, "tools", "dynamic")
        os.makedirs(self.dynamic_dir, exist_ok=True)
        
        # Hydrate dynamic skills immediately upon boot
        self.registry.scan_and_register_directory(self.dynamic_dir)
        
    async def download_skill(self, raw_url: str, skill_name: str) -> bool:
        """Downloads an external agentskills.io format python file and injects it."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(raw_url) as resp:
                    if resp.status != 200:
                        logger.error(f"[SkillManager] Failed downloading skill {skill_name}: HTTP {resp.status}")
                        return False
                    
                    code_content = await resp.text()
                    
                    file_path = os.path.join(self.dynamic_dir, f"{skill_name}.py")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(code_content)
                        
                    logger.info(f"[SkillManager] Saved {skill_name} to {file_path}")
                    
            # Rehydrate the registry immediately 
            self.registry.scan_and_register_directory(self.dynamic_dir)
            return True
        except Exception as e:
            logger.error(f"[SkillManager] Exception downloading {skill_name}: {e}")
            return False
