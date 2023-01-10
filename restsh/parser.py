from typing import cast, List, Tuple, Type, Union, Any, Optional
from .token import Token, Sym, Op, Eq, Dot, LParen, RParen, LBrace, RBrace, LBracket, RBracket \
    , Comma, Colon, SemiColon, Bang, BSlash \
    , If, Then, Else, Let, Imp, Help, Ext, Try, Str, Flt, Int
from .evaluate import Eval, Variable, ObjectRef, Define, Float, Integer, String, Array, Assignment, Import \
    , Arg, ArgList, Call, OpCall, ElementList, DictObject, Subscript, Not, ParamList, Closure \
    , IfThen, Describe, Exit, TryException, Group, Block

class EndOfTokens(Exception):
    pass

class ParseError(Exception):
    def __init__(self, tokens:List[Union[Type[Token], Type[Eval]]]) -> None:
        super().__init__()
        self.tokens = tokens


Rule = Tuple[Type[Eval], List[Union['Production', Type[Token], Type[Eval]]]]
ParseStack = List[Union[Eval, Token]]

class ParseResult:
    def __init__(self, length:int) -> None:
        self.length = length

    @property
    def failed(self) -> bool:
        return False

    def __lt__(self, other:'ParseResult') -> bool:
        if isinstance(self, FailedParse) or isinstance(other, FailedParse):
            return False
        elif isinstance(self, FullParse):
            # FullPase that read the entire stack - can't get a better parse
            if self.stackEmpty:
                return False
            # Special case other:PartialParse here?
            # Otherwise, we want the parse that ate the most tokens
            else:
                return self.length < other.length
        elif isinstance(self, PartialParse):
            # If this is a partial parse, and the rhs is a Full and complete parse, take the rhs
            if isinstance(other, FullParse) and other.stackEmpty:
                return True
            else:
                return self.length < other.length
        else:
            return self.length < other.length

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.length}>'

class FullParse(ParseResult):
    def __init__(self, parsed:Eval, stack:List[Union[Eval, Token]], length:int) -> None:
        super().__init__(length)
        self.stack:List[Union[Eval, Token]] = list(stack)
        self.parsed = parsed

    @property
    def stackEmpty(self) -> bool:
        return len(self.stack) < 1

    def __repr__(self) -> str:
        return f'FullParse<{self.parsed}, {self.stack}, {self.length}>'
        
class PartialParse(ParseResult):
    def __init__(self, of:'Production', length:int) -> None:
        super().__init__(length)
        self.of = of

    @property
    def stack(self) -> bool:
        return []

    @property
    def stackEmpty(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.of.name}, {self.length}>'

class FailedParse(ParseResult):
    def __init__(self, expecting:List[Union[Type[Eval], Type[Token]]], length:int) -> None:
        super().__init__(length)
        self.expecting = expecting

    @property
    def failed(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f'FailedParse<{self.expecting}, {self.length}>'


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
            recursed:List[Tuple['Production',int]],
            tokenCount
            , offset
            ) -> ParseResult: #Tuple[Eval, ParseStack, bool]:

        match:List[Union[Eval, Token]] = []
        parsedResult:Optional[ParseResult] = None

        print(' '*offset, f'Parsing rule: {rule} on stack {stack}')

        for pat in rule[1]:
            if not stack:
                print(' '*offset, f' > EOT {self.name}: {rule[1]}')
                parsedResult = PartialParse(self, tokenCount)
                break

            if isinstance(pat, Production):
                result = pat.parse(stack, recursed, tokenCount, offset+1)

                if isinstance(result, FullParse):
                    tokenCount = result.length
                    match.append(result.parsed)
                    stack = result.stack
                else:
                    parsedResult = result
                    break

            elif isinstance(stack[0], cast(Type[Any], pat)):
                if isinstance(stack[0], Eval):
                    print('Matched eval %s %s'% (stack[0], pat))
                tokenCount += 1
                match.append(stack[0])
                stack = stack[1:]
                recursed = []
            else:
                parsedResult = FailedParse([pat], tokenCount)
                break


        if parsedResult is None:
            parsedResult = FullParse(cast(Any, rule[0]).parse(*match), stack, tokenCount)
            print(' '*offset, f'Parsed {rule[0]} as {parsedResult}')

        return parsedResult


    def parseRight(self,
            stack:ParseStack,
            recursed:List[Tuple['Production',int]],
            tokenCount:int,
            offset:int
            ) -> ParseResult:
        error:List[FailedParse] = []
        longestMatch:Optional[ParseResult] = None
        #print(' '*offset, '%s (%s): %s' % (self.name or 'TOKENS', recursed, stack))

        for rule, index in zip(self.rules, range(len(self.rules))):
            print(' '*offset, f' {self.name} rule: {index}')
            if (self, index) in recursed:
                print(f'   Recursed? ({self}, {index}) in [{recursed}]')
                continue

            if isinstance(rule, Production):
                match = rule.parse(stack, [(self, index), *recursed], tokenCount, offset+1)
            else:
                match = self.parseRule(rule, stack, [(self, index), *recursed], tokenCount, offset+1)

            if isinstance(match, FailedParse):
                error.append(match)

            elif longestMatch is None or longestMatch < match:
                longestMatch = match


        # If there is either no matching rule, or the matching rule leaves items on the stack
        if not longestMatch:
            expecting:List[Union[Type[Token], Type[Eval]]] = []

            for err in error:
                expecting = expecting + err.expecting

            longestMatch = FailedParse(expecting, tokenCount)


        print(' '*offset, '-> lM %s' % (longestMatch,))

        return longestMatch


    def parse(self, stack:ParseStack, recursed:List[Tuple['Production',int]], tokenCount:int, offset:int) -> ParseResult:
        finalResult:Optional[ParseResult] = None

        # This loop essentially implements a non-advancing transition, in the special case of left recursion (without a
        # start symbol).
        # It's a little clunky, but it works (sorta).

        while stack:
            print(' '*offset, 'Parsing %s with stack %s' % (self, stack))
            result = self.parseRight(stack, recursed, tokenCount, offset+1)
            print(' '*offset, 'parseRight result %s' % result)

            #if isinstance(result, FullParse):
            if not result.failed and (finalResult is None or finalResult < result):
                finalResult = result
                stack = result.stack
                tokenCount = result.length
                # I don't like that this check is required.
                if stack and stack[0] != result.parsed:
                    stack.insert(0, result.parsed)
                #print('%s read interim result %s (%s); reparsing: %s' % (self, result, result.__class__, stack))
            else:
                break

            #print(' '*offset, f' < parsed {self.name}, stack: {stack}')

        if isinstance(result, FullParse):
            # Now that we've fully parsed this Production, we can push its result into the stack
            finalResult.stack = finalResult.stack[:1]

        print(' '*offset, f'* Returning {self.name} parse result {finalResult}')
        return finalResult or PartialParse(self, tokenCount)


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
    #array,
    #dictObject,
    #constant,
    #closure,
    #boolean,
    ## Left recursive
    #tryex,
    #ifthen,
    #subscript,
    #call,
    #opcall,
    #group,
    #block,
    objectRef,
    )
    

statement = Production(
    #describe,
    #ext,
    #imprt,
    #define,
    #assignment,
    expression,
    name='statement'
    )


# TODO: Need a more nuanced way to communicate partial results than exceptions
def parse(tokens:List[Token]) -> List[Eval]:
    stack = cast(ParseStack, tokens)

    result = statement.parse(stack, [], 0, 0)

    if isinstance(result, PartialParse):
        raise EndOfTokens()

    elif isinstance(result, FailedParse):
        raise ParseError(result.expecting)

    elif not cast(FullParse, result).stackEmpty:
        print('Raising ParseError because of left-over stack: %s' % (stack,))
        raise ParseError([])

    return [cast(FullParse, result).parsed]

