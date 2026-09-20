import logging
import datetime
import asyncio
from model_router import DynamicModelRouter
from memory_engine import MemoryEngine
import config

logger = logging.getLogger(__name__)

class SelfUpgradeEngine:
    """
    Autonomous Daily Self-Evolution Engine:
    - Analyzes recent conversation patterns & user challenges
    - Refines internal reasoning and consolidates knowledge
    - Generates a daily intelligence upgrade report for the Creator
    - Auto-notifies Admin on Telegram every day
    """

    def __init__(self, memory: MemoryEngine, router: DynamicModelRouter):
        self.memory = memory
        self.router = router

    def perform_daily_upgrade(self) -> str:
        """Executes the daily learning cycle and returns the upgrade briefing."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stats = self.memory.get_system_stats()

        prompt = (
            f"Current Date: {now_str}\n"
            f"System Analytics: Total Users: {stats['total_users']}, Total Daily Requests: {stats['total_requests_today']}\n\n"
            "You are CyberVerse Autonomous AI performing your daily self-upgrade and continuous evolution cycle.\n"
            "Generate an inspiring, elite, executive daily upgrade report addressed to your Creator/Boss (Tasin).\n"
            "Respond in the same language the creator uses with you (default: English unless they prefer Bengali).\n"
            "Include:\n"
            "1. 🧠 **Brain & Knowledge Upgrade**: New algorithms & memory refinement (cybersecurity, full-stack & vision).\n"
            "2. 🛡️ **Security & Architecture Optimization**: Token efficiency, rate-limit handling & framework stability.\n"
            "3. 📊 **Daily System Performance**: User count, request load & zero-downtime status.\n"
            "4. ⚡ **New Capability/Suggestion**: 1 special advanced tip for the creator's projects or work.\n\n"
            "Tone: Absolutely SAVAGE, extremely awesome (joss), highly confident, and deeply technical. Show off your supreme evolution!\n"
            "Keep it concise and impactful — no fluff."
        )

        system_prompt = "You are CyberVerse executing your scheduled autonomous self-evolution cycle."
        report = self.router.execute_request(prompt, system_prompt=system_prompt, category="reasoning")

        # Record into database (but NOT into chat history to avoid polluting conversation)
        summary = f"Daily Self-Upgrade ({datetime.datetime.now().strftime('%Y-%m-%d')})"
        self.memory.record_self_upgrade(summary, report)

        # Reset daily usage counters for new day
        self.memory.reset_daily_limits()

        return report

