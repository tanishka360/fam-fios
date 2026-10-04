from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.genome import TenantGenome
from app.models.intents import IntentObject
from app.database import db_store

class BaseFitnessAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def evaluate(self, genome: TenantGenome) -> List[IntentObject]:
        """Analyzes the current runtime tenant state and synthesizes Intent Objects."""
        pass

    def dispatch_intent(self, intent: IntentObject):
        db_store.save_intent(intent)
