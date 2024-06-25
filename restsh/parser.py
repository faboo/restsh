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
    def __init__(self, inside:'Production', tokens:List[Union[Type[Token], Type[Eval]]], endOfTokens:bool) -> None:
        super().__init__()
        self.inside = inside
        self.tokens = tokens
        self.endOfTokens = endOfTokens


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
            , offset
            ) -> Tuple[Eval, ParseStack, bool]:

        #print(' '*offset, 'parsing ', stack[0], ' with rule ', rule)

        eot = False
        parsed:List[Union[Eval, Token]] = []

        for pat in rule[1]:
            if not stack:
                #print(f' > EOT {self.name}: {rule[1]}')
                raise EndOfTokens(self)

            if isinstance(pat, Production):
                result, stack, endOfTokens = pat.parse(stack, recursed, offset+1)
                eot = eot or endOfTokens
            elif isinstance(stack[0], cast(Type[Any], pat)):
                #if isinstance(stack[0], Eval):
                    #print('Matched eval %s %s'% (stack[0], pat))
                result = stack[0]
                stack = stack[1:]
                recursed = []
                #print('    %s' % stack)
            else:
                raise ParseError(self, [pat], eot)

            parsed.append(result)

        return (rule[0].parse(*parsed), stack, eot) #type:ignore


    def parseRight(self, stack:ParseStack, recursed:List[Tuple['Production',int]], offset
            ) -> Tuple[Eval, ParseStack, bool]:
        eot = False
        error = []
        #matches:List[Tuple[Eval, ParseStack]] = []
        longestMatch:Optional[Tuple[Eval, ParseStack, bool]] = None
        #print(' '*offset, '%s (%s): %s' % (self.name or 'TOKENS', recursed, stack))

        for rule, index in zip(self.rules, range(len(self.rules))):
            try:
                if (self, index) in recursed:
                    continue

                if isinstance(rule, Production):
                    #matches.append(rule.parse(stack, [(self, index), *recursed], offset+1))
                    match = rule.parse(stack, [(self, index), *recursed], offset+1)
                else:
                    #matches.append(self.parseRule(rule, stack, [(self, index), *recursed], offset+1))
                    match = self.parseRule(rule, stack, [(self, index), *recursed], offset+1)

                # If we ran out of tokens, this *is* the longest match
                if not match[1]:
                    print(f'Ran out of tokens {self.name}, no exception: {match}')
                    longestMatch = match
                    break

                if match[2]:
                    eot = True

                if not longestMatch:
                    longestMatch = match
                elif len(longestMatch[1]) < len(match[1]):
                    longestMatch = match

            except ParseError as ex:
                error.append(ex)
                eot = eot or ex.endOfTokens
            except EndOfTokens:
                #print('Setting EOT in', self.name)
                eot = True

        # If there is either no matching rule, or the matching rule leaves items on the stack
        if not longestMatch:
            tokens:List[Union[Type[Token], Type[Eval]]] = []

            for err in error:
                tokens = tokens + err.tokens

            raise ParseError(self, tokens, eot)

        elif longestMatch[1] and eot:
            print(" -> END OF TOKENS %s, %s" % (self.name, longestMatch))
            raise EndOfTokens(self)

        if eot:
            print(f'Match but EOT, {self.name}: {longestMatch}')

        #print(' '*offset, '-> lM %s' % (longestMatch,))

        return cast(Tuple[Eval, ParseStack, bool], longestMatch)


    # TODO: Named tuple result? Class?
    def parse(self, stack:ParseStack, recursed:List[Tuple['Production',int]], offset) -> Tuple[Eval, ParseStack, bool]:
        fullResult:Optional[Tuple[Eval, ParseStack], bool] = None

        # This loop essentially implements a non-advancing transition, in the special case of left recursion (without a
        # start symbol).
        # It's a little clunky, but it works.

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
            print('End of tokens')
            if not fullResult:
                print(f'Unwinding end of tokens:  {ex.inside.name}, stack: {fullResult and fullResult[1]}')
                raise
            elif fullResult[1]:
                raise ParseError(self, [], True)
        except Exception as ex:
            print(f'ex: {ex.__class__}, {ex.inside.name}, {ex.endOfTokens}')
            if not fullResult:
                raise

        print(f'* Returning {self.name} parse result {fullResult}')
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
    define,
    assignment,
    expression,
    name='statement'
    )


# TODO: Need a more nuanced way to communicate partial results than exceptions
def parse(tokens:List[Token]) -> List[Eval]:
    results = []
    stack = cast(ParseStack, tokens)

    result, stack, endOfTokens = statement.parse(stack, [], 0)

    if stack:
        print('Raising ParseError because of left-over stack; endOfTokens: ', endOfTokens)
        print('stack: %s', stack)
        raise ParseError(None, [], endOfTokens)

    results.append(result)

    return results

