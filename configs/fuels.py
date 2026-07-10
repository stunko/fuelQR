from dataclasses import dataclass, InitVar


@dataclass
class BaseFuel:
    payloads: InitVar[list[dict]] = None
    id: str = None
    code: str = None
    title: str = None
    percent: int = 0
    addresses: list = ""

    def __post_init__(self, payloads: list[dict]) -> None:
        if payloads:
            self.percent = sum(s[f"{self.title}_percent"] for s in payloads if
                               isinstance(s[f"{self.title}_percent"],
                                          (int, float)))
            self.addresses = [s["address"] for s in payloads if
                              s[f"{self.title}_percent"]]


@dataclass
class A92(BaseFuel):
    id: int = "3"
    title: str = "a92"
    code: str = "a92"


@dataclass
class A95(BaseFuel):
    id: int = "4"
    title: str = "a95"
    code: str = "a95"


@dataclass
class A95Ultra(BaseFuel):
    id: int = "5"
    title: str = "a95_ultra"
    code: str = "a95_plus"


@dataclass
class A100(BaseFuel):
    id: int = "6"
    title: str = "a100"
    code: str = "a100"


@dataclass
class Diesel(BaseFuel):
    id: int = "1"
    title: str = "diesel"
    code: str = "dt"


@dataclass
class DieselUltra(BaseFuel):
    id: int = "2"
    title: str = "diesel_ultra"
    code: str = "dt_plus"
