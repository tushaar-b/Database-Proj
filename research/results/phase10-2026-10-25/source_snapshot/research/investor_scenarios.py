from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Scenario:
    name: str
    surplus_group: str
    tier: str
    income: float
    mandatory: float
    discretionary: float
    reserve: float
    initial_cash: float = 100000.

    @property
    def buffer(self):
        return max(0., self.income - self.mandatory - self.reserve)


def scenarios():
    groups = {'low': (45000,30000,3000,10000), 'medium': (100000,50000,10000,30000),
              'high': (250000,90000,30000,60000)}
    return [Scenario(f'{g}_{t.lower()}', g, t, *v) for g,v in groups.items()
            for t in ['CONSERVATIVE','MODERATE','AGGRESSIVE']]
