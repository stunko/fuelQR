from dataclasses import dataclass, InitVar


@dataclass
class BaseFuel:
    payloads: InitVar[list[dict]]
    title: str = None
    percent: int = None
    addresses: list = None

    def __post_init__(self, payloads: list[dict]) -> None:
        self.percent = sum(s[f"{self.title}_percent"] for s in payloads if
                           isinstance(s[f"{self.title}_percent"],
                                      (int, float)))
        self.addresses = [s["address"] for s in payloads if
                          s[f"{self.title}_percent"]]


@dataclass
class A92(BaseFuel):
    title: str = "a92"


@dataclass
class A95(BaseFuel):
    title: str = "a95"


@dataclass
class A95Ultra(BaseFuel):
    title: str = "a95_ultra"


@dataclass
class Diesel(BaseFuel):
    title: str = "diesel"


@dataclass
class DieselUltra(BaseFuel):
    title: str = "diesel_ultra"
