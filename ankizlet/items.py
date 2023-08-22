from dataclasses import dataclass, field


@dataclass
class Card:
    front: str
    back: str
    image: str
    f_audio: str
    b_audio: str


@dataclass
class Deck:
    title: str
    cards: list = field(default_factory=list)
