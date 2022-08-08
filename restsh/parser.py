from typing import cast, List, Tuple, Type, Union, Any, Optional
from .token import Token, Sym, Op, Eq, Dot, LParen, RParen, LBrace, RBrace, LBracket, RBracket \
    , Comma, Colon, SemiColon, Bang, BSlash \
    , Let, Imp, Help, Ext, Try, Str, Flt, Int
from .evaluate import Eval, Variable, ObjectRef, Define, Float, Integer, String, Array, Assignment, Import \
    , Arg, ArgList, Call, OpCall, ElementList, DictObject, Subscript, Not, ParamList, Closure \
    , Describe, Exit, TryException, Group, Block

class EndOfTokens(Exception):
    pass

class ParseError(Exception):
    def __init__(self, tokens:List[Type[Token]]) -> None:
        super().__init__()
        self.tokens = tokens


Rule = Tuple[Type[Eval], List[Union['Production', Type[Token]]]]
ParseStack = List[Union[Eval, Token]]

class Production:
    def __init__(self, *rules:Union['Production', Rule], **kwargs) -> None:
        self.name:str = str(kwargs.get('name') or '') # TODO: random name
        self.rules:List[Union['Production', Rule]] = list(rules)


    def __eq__(self, other:Any) -> bool:
        return isinstance(other, Production) and other.name == self.name


    def __hash__(self) -> int:
        return hash(self.name)


    def extend(self, *rules:Union['Production', Rule]) -> None:
        self.rules = self.rules + list(rules)

    def lookAheadRule(self, recursed:List[Tuple['Production',int]], token:Union[Token, Eval], rule:Union['Production', Rule]) -> bool:
        if isinstance(rule, Production):
            return cast(Production, rule).lookAhead(recursed, token)
        else:
            ruleList = rule[1]

            if not ruleList:
                return True
            elif isinstance(ruleList[0], type(Token)) and issubclass(ruleList[0], Token):
                return isinstance(token, ruleList[0])
            else:
                return cast(Production, ruleList[0]).lookAhead(recursed, token)
        

    def lookAhead(self, recursed:List[Tuple['Production',int]], token:Union[Token, Eval]) -> bool:
        for index in range(len(self.rules)):
            rule = self.rules[index]
            if self.lookAheadRule([(self, index), *recursed], token, rule):
                return True
        return False

    def parseRule(self,
            rule:Rule,
            stack:ParseStack,
            recursed:List[Tuple['Production',int]]
            , offset
            ) -> Tuple[Eval, ParseStack]:

        #print(' '*offset, 'parsing ', stack[0], ' with rule ', rule)

        parsed:List[Union[Eval, Token]] = []

        for pat in rule[1]:
            if not stack:
                #print(' > EOT %s' % rule[1])
                raise EndOfTokens()

            if isinstance(pat, Production):
                result, stack = pat.parse(stack, recursed, offset+1)
            elif isinstance(stack[0], cast(Type[Any], pat)):
                result = stack[0]
                stack = stack[1:]
                recursed = []
                #print('    %s' % stack)
            else:
                raise ParseError([pat]) #TODO: include expected token etc.

            parsed.append(result)

        return (rule[0].parse(*parsed), stack) #type:ignore


    def parse(self, stack:ParseStack, recursed:List[Tuple['Production',int]], offset) -> Tuple[Eval, ParseStack]:
        eot = False
        error = []
        matches:List[Tuple[Eval, ParseStack]] = []
        longestMatch:Optional[Tuple[Eval, ParseStack]] = None
        #print(' '*offset, '%s (%s): %s' % (self.name or 'TOKENS', recursed, stack))

        for rule, index in zip(self.rules, range(len(self.rules))):
            try:
                if (self, index) in recursed:
                    continue
                #if not self.lookAheadRule(recursed, stack[0], rule):
                #    continue

                if isinstance(rule, Production):
                    #if rule.lookAhead(recursed):
                    matches.append(rule.parse(stack, [(self, index), *recursed], offset+1))
                else:
                    #if not rule[1] or rule[1][0] not in recursed:
                    matches.append(self.parseRule(rule, stack, [(self, index), *recursed], offset+1))

                # If we ran out of tokens, this *is* the longest match
                if matches and not matches[-1][1]:
                    break

            except ParseError as ex:
                error.append(ex)
            except EndOfTokens:
                eot = True

        if not matches:
            if eot:
                raise EndOfTokens()
            
            tokens:List[Type[Token]] = []

            for err in error:
                tokens = tokens + err.tokens

            raise ParseError(tokens)

        for match in matches:
            # smallest leftover token list, means longest match
            # but take the *first* of the smallest matches
            #pylint: disable=unsubscriptable-object
            if longestMatch is None or len(longestMatch[1]) > len(match[1]):
                longestMatch = match

        #print(' '*offset, '-> %s' % (longestMatch,))
        return cast(Tuple[Eval, ParseStack], longestMatch)


    def __repr__(self) -> str:
        return 'Prod[%s]' % self.name if self.name else 'Prod[UNKNOWN]'


def getStartSymbols(parser, knownStarts=None):
    knownStarts = knownStarts or {}
    startSymbols = []

    for rule in parser.rules:
        if isinstance(rule, Production):
            start = rule
        elif not rule[1]:
            start = None
        else:
            start = rule[1][0]

        if isinstance(start, Production):
            if start.name not in knownStarts:
                knownStarts[start.name] = []
                knownStarts[start.name] = getStartSymbols(start, knownStarts)

            startSymbols = startSymbols + knownStarts[start.name]

        else:
            startSymbols.append(start)

    return startSymbols


def getStartTable(parser, knownStarts=None):
    knownStarts = knownStarts or {}
    startTable = {}

    for rule in parser.rules:
        if isinstance(rule, Production):
            for symbol, evls in getStartTable(rule, knownStarts).items():
                if symbol not in startTable:
                    startTable[symbol] = set()

                startTable[symbol].update(evls)
        else:
            if not rule[1]:
                start = None
            else:
                start = rule[1][0]

            startSymbols = []

            if isinstance(start, Production):
                if start.name not in knownStarts:
                    knownStarts[start.name] = []
                    knownStarts[start.name] = getStartSymbols(start, knownStarts)

                startSymbols = startSymbols + knownStarts[start.name]

            else:
                startSymbols.append(start)

            for symbol in startSymbols:
                if symbol not in startTable:
                    startTable[symbol] = set()

                startTable[symbol].add(rule[0])

    return startTable

    
    
    


expression = Production(name='expression')

constant = Production(
    (String, [Str]),
    (Integer, [Int]),
    (Float, [Flt]),
    name='constant'
    )

boolean = Production(
    (Not, [Bang, expression]),
    name='boolean'
    )

variable = Production(
    (Variable, [Sym]),
    name='variable'
    )

operator = Production(
    (Variable, [Op]),
    name='operator'
    )

objectRef = Production(name='objectRef')
objectRef.extend(
    (ObjectRef, [variable, Dot, Sym]),
    (ObjectRef, [expression, Dot, Sym]),
    )

elementList = Production(name='elementList')
elementList.extend(
    (ElementList, [expression, Comma, elementList]),
    (ElementList, [expression]),
    (ElementList, []),
    )

array = Production(
    (Array, [LBracket, elementList, RBracket]),
    name='array'
    )

paramList = Production(name='paramList')
paramList.extend(
    (ParamList, [Sym, Comma, paramList]),
    (ParamList, [Sym]),
    (ParamList, []),
    )

closure = Production(
    (Closure, [BSlash, paramList, Dot, expression]),
    name='closure'
    )


arg = Production(
    (Arg, [Sym, Colon, expression]),
    name='arg'
    )

argList = Production(name='argList')
argList.extend(
    (ArgList, [arg, Comma, argList]),
    (ArgList, [arg]),
    (ArgList, []),
    )

dictObject = Production(
    (DictObject, [LBrace, argList, RBrace]),
    name='dictObject'
    )

call = Production(
    (Call, [variable, LParen, argList, RParen]),
    (Call, [objectRef, LParen, argList, RParen]),
    name='call'
    )

opcall = Production(
    (OpCall, [expression, operator, expression]),
    name='opcall'
    )

tryex = Production(
    (TryException, [Try, expression]),
    name='try'
    )

subscript = Production(
    (Subscript, [variable, LBracket, expression, RBracket]),
    name='subscript'
    )


group = Production(
    (Group, [LParen, expression, RParen]),
    name='group'
    )

define = Production(
    (Define, [Let, variable]),
    name='define'
    )

lvalue = Production(
    define,
    objectRef,
    variable,
    name='lvalue'
    )

rvalue = Production(
    expression,
    name='rvalue'
    )

describe = Production(
    (Describe, [Help, Sym]),
    (Describe, [Help]),
    name='describe'
    )

ext = Production(
    (Exit, [Ext]),
    name='exit'
    )

imprt = Production(
    (Import, [Imp, Sym]),
    name='import'
    )


assignment = Production(
    (Assignment, [lvalue, Eq, rvalue]),
    name='assignment'
    )


block = Production(
    (Block, [expression, SemiColon, expression]),
    name='block'
    )


expression.extend(
    variable,
    array,
    dictObject,
    constant,
    closure,
    boolean,
    # Left recursive
    tryex,
    objectRef,
    subscript,
    call,
    opcall,
    group,
    block,
    )
    

statement = Production(
    describe,
    ext,
    imprt,
    define,
    assignment,
    expression,
    name='statement'
    )


def parse(tokens:List[Token]) -> List[Eval]:
    results = []
    stack = cast(ParseStack, tokens)

    while stack:
        result, stack = statement.parse(stack, [], 0)
        results.append(result)

    return results
