from typing import cast, List, Set, Dict, Union, Tuple, Optional, Any, Type
from inspect import getfullargspec
from .token import Token
from .evaluate import Eval
from .parser import Production, Rule

Term = Union[Token, Eval]
TermType = Union[Type[Token], Type[Eval]]

class ParseError(Exception):
    pass


class State:
    def __init__(self, id:int, prev:int, term:Term, lookahead:Set[TermType]) -> None:
        self.id = id
        self.prev = prev
        self.term = term
        self.lookahead = lookahead

    def hasLookahead(self, term:Term) -> bool:
        for lahead in self.lookahead:
            if isinstance(term, lahead):
                return True
        return False

    def goto(self, parser:'Parser') -> None:
        pass


class Reduce(State):
    def __init__(self, prev:int, term:Term, lookahead:Set[TermType], reducer:Eval) -> None:
        super().__init__(prev, term, lookahead)
        self.reducer = reducer
        self.length = len(getfullargspec(reducer).args)

    def goto(self, parser:'Parser') -> None:
        pos = parser.position + 1
        terms = parser.stream[pos-self.length : pos]
        parser.position -= self.length
        parser.stream[pos-self.length : pos] = self.reducer(*terms)


class Shift(State):
    def goto(self, parser:'Parser') -> None:
        parser.position += 1


class Parser:
    def __init__(self, grammar:Grammar, tokens:List[Token]) -> None:
        self.grammar = grammar
        self.stream:List[Term] = cast(List[Term], list(tokens))
        self.state = 0
        self.position = 0


    def parse(self) -> Eval:
        while True:
            term = self.stream[self.position]
            lookahead = self.stream[self.position + 1] \
                if self.position + 1 < len(self.stream) \
                else None # EOF

            state = grammar.findAction(self.state, term, lookahead)

            if state:
                state.goto(self)
                self.state = state.id
            else:
                return self.stream[0]


class Grammar:
    def __init__(self, start:Production) -> None:
        self.states:List[] = [ ]
        # Indexes are what state we're transitioning from
        self.table:List[Dict[]] = [ ]

        self.buildTable(start)


    def findAction(self, state:int, term:Term, lookahead:Term) -> Rule:
        states = self.table[state][term.__class__]

        for state in states:
            if state.hasLookahead(lookahead):
                return state
        raise ParseException('Unexpected %s', lookAhead)


    def buildItemSet(itemSet:list, prod:Production) -> None:
        items:list = []

        for rule in prod.rules:
            expRule = (prod.name, None, [rule]) \
                if isinstance(rule, Production) \
                else (prod.name, *rule)
            itemSet.append((prod, expRule))
            items.append(expRule)


        for rule in items:
            for item in rule[1]:
                if isinstance(item, Production):
                    self.buildItemSet(itemSet, item)


    def buildStates(self, itemSet:list) -> None:
        

        for item in itemSet:
            self.


    def buildTable(self, start:Production) -> None:
        itemSet:list = [ ]

        self.buildItemSet(itemSet, start)

        self.buildStates(itemSet)
        
        

    def parse(self, tokens:List[Token]) -> Eval:
        parser = Parser(self, tokens)

        return parser.parse()
