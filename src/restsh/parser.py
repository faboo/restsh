from typing import cast, List, Tuple, Type, Union, Any, Optional
from .token import Token, Sym, Op, Eq, Dot, LParen, RParen, LBrace, RBrace, LBracket, RBracket \
    , Comma, Colon, SemiColon, Bang, BSlash \
    , If, Then, Else, Let, Imp, Help, Ext, Try, Str, Flt, Int
from .evaluate import Eval, Variable, ObjectRef, Define, Float, Integer, String, Array, Assignment, Import \
    , Arg, ArgList, Call, OpCall, ElementList, DictObject, Subscript, Not, ParamList, Closure \
    , IfThen, Describe, Exit, TryException, Group, Block

class EndOfTokens(Exception):
    def __init__(self, inside:'Production') -> None:
        super().__init__()
        self.inside = inside

class ParseError(Exception):
    def __init__(self,
            inside:Optional['Production'],
            tokens:List[Union[Type[Token],
            Type[Eval]]],
            endOfTokens:bool
            ) -> None:
        super().__init__()
        self.inside = inside
        self.tokens = tokens
        self.endOfTokens = endOfTokens


class PartialParseError(Exception):
    def __init__(self, inside:'Production') -> None:
        super().__init__()
        self.inside = inside


Rule = Tuple[Type[Eval], List[Union['Production', Type[Token], Type[Eval]]]]
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


    def parseRule(self,
            rule:Rule,
            stack:ParseStack,
            recursed:List[Tuple['Production',int]]
            , offset:int
            ) -> Tuple[Eval, ParseStack, bool]:

        eot = False
        parsed:List[Union[Eval, Token]] = []
        openParse = False

        for pat in rule[1]:
            # If we have pattern left, and our token/Eval stack is empty, then we have a partial parse
            if not stack:
                #print(f' > EOT {self.name}: {pat}')
                if openParse:
                    raise PartialParseError(self)
                else:
                    raise EndOfTokens(self)

            if isinstance(pat, Production):
                result, stack, endOfTokens = pat.parse(stack, recursed, offset+1)
                eot = eot or endOfTokens

            elif isinstance(stack[0], cast(Type[Any], pat)):
                if issubclass(pat, Token):
                    openParse |= pat.openParse

                result = stack[0]
                stack = stack[1:]
                recursed = []
            # This token/Eval doesn't match this part of the pattern
            else:
                raise ParseError(self, [pat], eot)

            parsed.append(result)

        return (rule[0].parse(*parsed), stack, eot) #type:ignore


    def parseRight(self, stack:ParseStack, recursed:List[Tuple['Production',int]], offset:int
            ) -> Tuple[Eval, ParseStack, bool]:
        eot = False
        partial:PartialParseError|None = None
        error = []
        longestMatch:Optional[Tuple[Eval, ParseStack, bool]] = None

        for rule, index in zip(self.rules, range(len(self.rules))):
            try:
                if (self, index) in recursed:
                    continue

                if isinstance(rule, Production):
                    match = rule.parse(stack, [(self, index), *recursed], offset+1)
                else:
                    match = self.parseRule(rule, stack, [(self, index), *recursed], offset+1)

                if match[2]:
                    eot = True

                if longestMatch is None:
                    #print(' '*offset, f'setting longest match: {match}')
                    longestMatch = match
                # the longest match is the one that leaves the least tokens
                elif len(longestMatch[1]) > len(match[1]):
                    #print(' '*offset, f'updating longest match: {match}')
                    longestMatch = match

            #except PartialParseError as ex:
                # We ran out of tokens mid-parse, so if we don't have a complete parse, this would be the longest parse
            #    partial = ex
            except ParseError as ex:
                error.append(ex)
            except EndOfTokens:
                #print('Setting EOT in', self.name)
                eot = True

        # If there is either no matching rule, or the matching rule leaves items on the stack
        if not longestMatch:
            # We had a partial match
            if partial is not None:
                raise partial

            # Otherwise, collect our expected tokens for a parse error

            tokens:List[Union[Type[Token], Type[Eval]]] = []

            for err in error:
                tokens = tokens + err.tokens

            raise ParseError(self, tokens, eot)

        # Our longest match leaves tokens/Evel left to parse
        elif longestMatch[1] and partial is not None:
            #print(" -> END OF TOKENS %s, %s" % (self.name, longestMatch))
            raise partial #pylint: disable=raising-bad-type

        #print(' '*offset, '-> lM %s' % (longestMatch,))

        return cast(Tuple[Eval, ParseStack, bool], longestMatch)


    def parse(self, stack:ParseStack, recursed:List[Tuple['Production',int]], offset) -> Tuple[Eval, ParseStack, bool]:
        fullResult:Tuple[Eval, ParseStack, bool]|None = None

        # This loop essentially implements a non-advancing transition, in the special case of left recursion (without a
        # start symbol).
        # It's a little clunky, but it works.

        #print(' '*offset, f'@ Trying {self.name}')
        try:
            while stack:
                #print('Parsing %s with stack %s' % (self, stack))
                result, stack, endOfTokens = self.parseRight(stack, recursed, offset)
                fullResult = (result, list(stack), endOfTokens)
                #print('storing full result: ', fullResult)

                if not endOfTokens:
                    stack.insert(0, result)
                #print('%s read interim result %s (%s); reparsing: %s' % (self, result, result.__class__, stack))
        except EndOfTokens as ex:
            #print('End of tokens')
            if fullResult is None:
                #print(f'Unwinding end of tokens:  {ex.inside.name}, stack: {fullResult and fullResult[1]}')
                raise
            elif fullResult[1]:
                raise ParseError(self, [], True) from ex
        except ParseError:
            #print(f'ex: {ex.__class__}, {ex.inside.name}, {ex.endOfTokens}')
            if not fullResult:
                raise

        #print(' '*offset, f'* Returning {self.name} parse result {fullResult}')
        return cast(Tuple[Eval, ParseStack, bool], fullResult)


    def __repr__(self) -> str:
        return 'Prod[%s]' % self.name if self.name else 'Prod[UNKNOWN]'


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
    #(ObjectRef, [variable, Dot, Sym]),
    (ObjectRef, [Eval, Dot, Sym]),
    )

elementList = Production(name='elementList')
elementList.extend(
    (ElementList, [ElementList, Comma, expression]),
    (ElementList, [expression]),
    )

array = Production(
    (Array, [LBracket, elementList, RBracket]),
    (Array, [LBracket, RBracket]),
    name='array'
    )


paramList = Production(name='paramList')
paramList.extend(
    (ParamList, [ParamList, Comma, Sym]),
    (ParamList, [Sym]),
    )

closure = Production(
    (Closure, [BSlash, paramList, Dot, expression]),
    (Closure, [BSlash, Dot, expression]),
    name='closure'
    )


arg = Production(
    (Arg, [Sym, Colon, expression]),
    name='arg'
    )

argList = Production(name='argList')
argList.extend(
    (ArgList, [ArgList, Comma, arg]),
    (ArgList, [arg]),
    )

dictObject = Production(
    (DictObject, [LBrace, argList, RBrace]),
    (DictObject, [LBrace, RBrace]),
    name='dictObject'
    )

call = Production(
    (Call, [expression, LParen, argList, RParen]),
    #(Call, [expression, LParen, elementList, Comma, argList, RParen]),
    (Call, [expression, LParen, elementList, RParen]),
    (Call, [expression, LParen, RParen]),
    name='call'
    )

opcall = Production(
    (OpCall, [Eval, operator, expression]),
    name='opcall'
    )

tryex = Production(
    (TryException, [Try, expression]),
    name='try'
    )

subscript = Production(
    (Subscript, [Eval, LBracket, expression, RBracket]),
    name='subscript'
    )


group = Production(
    (Group, [LParen, expression, RParen]),
    name='group'
    )

ifthen = Production(
    (IfThen, [If, expression, Then, expression, Else, expression]),
    name='ifthen'
    )

define = Production(
    (Define, [Let, variable]),
    name='let'
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
    (Describe, [Help, expression]),
    (Describe, [Help]),
    name='help'
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
    (Block, [Eval, SemiColon, expression]),
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
    ifthen,
    subscript,
    call,
    opcall,
    group,
    block,
    objectRef,
    )
    

statement = Production(
    describe,
    ext,
    imprt,
    assignment,
    define,
    expression,
    name='statement'
    )


# TODO: Need a more nuanced way to communicate partial results than exceptions
def parse(tokens:List[Token]) -> List[Eval]:
    results = []
    stack = cast(ParseStack, tokens)

    result, stack, endOfTokens = statement.parse(stack, [], 0)

    if stack:
        #print('Raising ParseError because of left-over stack; endOfTokens: ', endOfTokens)
        #print('stack: %s', stack)
        raise ParseError(None, [], endOfTokens)

    results.append(result)

    return results

