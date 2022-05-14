from hypatia.utility.constants import (
    ModelMode,
    TopologyType
)
from typing import (
    Dict,
    List,
    Optional
)

class Constraint():
    # Modes this constraint applies to
    MODES = [ModelMode.Planning, ModelMode.Operation]
    TOPOLOGY_TYPES = [TopologyType.SingleNode, TopologyType.MultiNode]

    def __init__(self, model_data, model_variables):
        self.model_data = model_data
        self.variables = model_variables

    # Public
    def get(self) -> List:
        if not Constraint.__matches_mode(self.__class__, self.model_data.settings):
            return {}

        self._check()

        return self.rules()

    def required_global_parameters(cls, settings) -> Dict:
        if not Constraint.__matches_mode(cls, settings):
            return {}

        return cls._required_global_parameters(settings)

    def required_trade_parameters(cls, settings) -> Dict:
        if not Constraint.__matches_mode(cls, settings):
            return {}

        return cls._required_trade_parameters(settings)

    def required_regional_parameters(cls, settings) -> Dict[str, Dict]:
        if not Constraint.__matches_mode(cls, settings):
            return {}

        return cls._required_regional_parameters(settings)

    # Protected
    def _check(self):
        pass

    def _rules(self) -> List:
        return []

    def _required_global_parameters(settings) -> Dict:
        return {}

    def _required_trade_parameters(settings) -> Dict:
        return {}

    def _required_regional_parameters(settings) -> Dict[str, Dict]:
        return {}

    # Private
    def __matches_mode(cls, settings) -> bool:
        if(settings.mode not in cls.MODES):
            return False

        if settings.multi_node:
            if TopologyType.MultiNode not in cls.TOPOLOGY_TYPES:
                return False
        else:
            if TopologyType.SingleNode not in cls.TOPOLOGY_TYPES:
                return False

        return True
