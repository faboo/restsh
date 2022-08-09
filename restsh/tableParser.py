from typing import cast, List, Dict, Union, Tuple, Optional, Any, Type
from .token import Token
from .evaluate import Eval
from .parser import Production, Rule, ParseStack


StreamT = Optional[Union[Type[Token],Type[Eval]]]


class State:
    StateNumber = 0

    def __init__(self, source:Any, ctor:Optional[Type[Any]]=None, collect:Optional[int]=None) -> None:
        self.number = State.StateNumber
        self.source = source
        self.ctor = ctor
        self.collect = collect
        State.StateNumber += 1
        #print('* STATE %s %s %s' % (self.number, source, ctor))

    def __eq__(self, other:Any) -> bool:
        return isinstance(other, State) and other.number == self.number

    def __hash__(self) -> int:
        return hash(self.number)

    def __repr__(self) -> str:
        source = self.source.__name__ if hasattr(self.source, '__name__') else self.source
        ctor = '(%s)' % self.ctor.__name__ if self.ctor else ''
        return 'STATE %s %s %s' % (self.number, source, ctor)

class CollectState(State):
    def __repr__(self) -> str:
        source = self.source.__name__ if hasattr(self.source, '__name__') else self.source
        ctor = '(%s)' % self.ctor.__name__ if self.ctor else ''
        return 'COLLECT %s %s %s' % (self.number, source, ctor)


class Parser:
    def __init__(self, start:Production) -> None:
        self.states:List[State] = []
        self.productionStart:Dict[Production, State] = { }
        self.productionEnd:Dict[Production, List[CollectState]] = { }
        self.transition:Dict[State, Dict[StreamT, State]] = { }

        self.processProduction(start)

        self.startState = self.productionStart[start]


    def addTransition(self, start:State, transitor:StreamT, lookahead:StreamT, end:State) -> None:
        #print(f'{start} -> {transitor}, {lookahead} -> {end}')
        transition = transitor

        if start not in self.transition:
            self.transition[start] = { }
        if transition not in self.transition[start]:
            self.transition[start][transition] = []

        #TODO: ?
        if end not in self.transition[start][transition]:
            #raise Exception(f'Duplicate transition from {start}, ({transitor}, {lookahead}) to {end}')

            self.transition[start][transition].append(end)


    def addFalseTransition(self, start:State, end:State) -> None:
        #print(f'{start} -> ____ -> {end}')
        for transitor, _ in self.transition[end]:
            self.addTransition(start, None, transitor, end)


    def processRule(self, start:State, rule:Rule) -> State:
        ctor, stream = rule
        state = start

        if stream:
            for index in range(len(stream)):
                transitor = stream[index]
                lookahead = stream[index+1] if index+1 < len(stream) else None

                if isinstance(transitor, Production):
                    end = self.processProduction(transitor)
                    self.addTransition(state, None, None, self.productionStart[transitor])
                    state = end

                else:
                    if lookahead is None:
                        end = State(transitor, ctor, len(stream))
                    else:
                        end = State(transitor)

                    self.states.append(end)

                    self.addTransition(state, transitor, lookahead, end)

                    state = end

        else:
            state = State(None, ctor, 0)
            self.states.append(state)
            self.addTransition(start, None, None, state)

        return state


    def processProduction(self, prod:Production) -> List[State]:
        if prod in self.productionEnd:
            return self.productionEnd[prod]

        start = State(prod)
        end = CollectState(prod)
        final:List[State] = []

        self.states.append(start)
        self.productionStart[prod] = start
        self.productionEnd[prod] = end
        self.states.append(end)

        for rule in prod.rules:
            if isinstance(rule, Production):
                final.append(self.processProduction(rule))
                self.addTransition(start, None, None, self.productionStart[rule])
            else:
                final.append(self.processRule(start, rule))

        for state in final:
            self.addTransition(state, None, None, end)

        return end


    def printTransitionTable(self) -> None:
        for state in self.states:
            print(str(state))

            if state in self.transition:
                transitions = self.transition[state]
                for transition, end in transitions.items():
                    transitor = transition.__name__ if transition else '-'
                    print('\t', transitor, ' -> ')
                    
                    for state in end:
                        print('\t\t', state)
            else:
                print('\tEND')


    def getTransition(self, state:State, transitor:StreamT) -> List[State]:
        transitions = self.transition[state]
        found = []

        print('transitions: %s' % transitions)

        if transitor.__class__ in transitions:
            found = transitions[transitor.__class__]
        elif None in transitions:
            for candidate in transitions[None]:
                try:
                    print('  %s candidate: %s' % (state, candidate))
                    found = self.getTransition(candidate, transitor)
                    if found:
                        break
                except:
                    pass

        if not found:
            raise Exception('Unexpected in state %s: %s' % (state, transitor))

        return found


    def parse(self, tokens:List[Token]) -> List[Eval]:
        results = []
        stack:ParseStack = cast(ParseStack, tokens)
        parsing:ParseStack = []
        stateStack:List[State] = []
        state = self.startState

        while stack:
            transitor = stack.pop(0)
            print(f'{state} -> {transitor}')
            possibleStates = self.getTransition(state, transitor)

            parsing.append(transitor)

            for nextState in possibleStates:

                if nextState.ctor:
                    print(f'\ncollecting {nextState.ctor.__name__}')
                    collect = parsing[-nextState.collect:]
                    parsing = parsing[:-nextState.collect]
                    parsing.append(nextState.ctor.parse(*collect))
                    print(f'\n           {parsing[-1]}')

                if isinstance(nextState, CollectState):
                   stack = parsing+stack
                   parsing = []

                if nextState.source:
                    results.push(state)

                state = nextState
                break

        print(f'PARSED: {parsing}')
        print(f'STACK: {stack}')
        print(f'STATE: {state}')
        return cast(List[Eval], parsing)
