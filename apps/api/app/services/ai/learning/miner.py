import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.message import Message
from app.db.session import AsyncSessionLocal
from app.services.ai.memory.memory_extractor import MemoryExtractor
from app.services.ai.providers.router import ProviderRouter

logger = logging.getLogger(__name__)

class TraceMinerLoop:
    """
    Decentralized Trace Miner mimicking OpenJarvis. 
    Instead of cryptographic PoW, it mines unstructured conversation logs 
    to extract structured behavioral patterns and memory facts natively.
    """
    def __init__(self, provider: ProviderRouter):
        self.provider = provider
        self.extractor = MemoryExtractor(provider)
        
    async def mine_batch(self, db: AsyncSession, batch_size: int = 10) -> int:
        """
        Pull recent user trajectories from the db and compress memory facts out of them.
        """
        stmt = (
            select(Message)
            .where(Message.role == "user")
            .order_by(Message.created_at.desc())
            .limit(batch_size)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        extracted_count = 0
        for msg in messages:
            try:
                # Re-using the memory extractor natively during downtime
                fact = await self.extractor.extract(msg.content)
                if fact:
                    # In a full implementation, we'd persist the memory item to the Memory table here.
                    logger.info(f"[Trace Miner] Extracted new artifact: {fact}")
                    extracted_count += 1
            except Exception as e:
                logger.warning(f"Trace mining fail on msg {msg.id}: {str(e)}")
                
        return extracted_count

    async def start(self, poll_interval: int = 300) -> None:
        """
        Downtime loop executing background mining of traces.
        """
        logger.info("Continuous Trace Learning Miner started.")
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    yielded = await self.mine_batch(db)
                    if yielded > 0:
                        logger.info(
                            f"Trace Miner round successful. "
                            f"Yielded {yielded} structural optimizations."
                        )
            except Exception as e:
                logger.error(f"Miner loop fatal error: {str(e)}")
            
            await asyncio.sleep(poll_interval)
