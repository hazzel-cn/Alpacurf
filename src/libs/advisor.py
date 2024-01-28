import dataclasses


# TODO: more dedicated structure
@dataclasses.dataclass(init=False)
class Advice:
    explanation: str


class Advisor:
    def __init__(self):
        pass

    def advise(self) -> Advice:
        raise NotImplementedError("method `advise` not implemented")
