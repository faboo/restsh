from token import Token
from evaluate import Eval
from parser import Production


def ParseState:
    StateNumber = 0

    def __init__(self) -> None:
        self.number = ParseState.StateNumber++

    def __eq__(self, other:Any) -> bool:
        return isinstance(ParseState, other) and other.number == self.number

    def __hash__(self) -> int:
        return hash(self.number)


def ParseTransition:
    def __init__(self, start:ParseState, end:ParseState, transitor:Union[Type[Token],Type[Eval]]) -> None:
        self.start = start
        self.end = end
        self.transitor = transitor


def Parser:
    productionStart:Dict[Production, ParseState ] = { }

    states:List[ParseState] = []

    def __init__(self, start:Production) -> None:
        self.startState = ParseState()
        self.states.append(self.startState)
        self.processProduction(self.startState, start)


    def processProduction(self, prod:Production) -> None:
        if prod in self.productionStart:
            return self.productionStart[rule]

        state = ParseState()

        for rule in prod.rules:
            if isinstance(rule, Production):
                nextState = self.processProduction(state, rule)
            else:
                constr, stream = rule



                
            
