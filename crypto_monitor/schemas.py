from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Account:
    name: str
    balances: dict[str, Decimal] = field(default_factory=dict)
