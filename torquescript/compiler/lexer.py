"""
    Lexer programming for the Torque Script parser.
"""
import re
import sys

class LexicalError(StandardError):
    pass

class Token(object):
    data = None
    line_number = None

    def __init__(self, match_data, line_number):
        self.line_number = line_number
        self.data = match_data.group(0) if type(match_data) is not str else match_data

    def __repr__(self):
        return "<%s token: %s on line %u>" % (self.__class__.__name__, repr(self.data), self.line_number)

class ArrayOpen(Token):
    PATTERN = re.compile("\\[")

class ArrayClose(Token):
    PATTERN = re.compile("\\]")

class Inheritance(Token):
    PATTERN = re.compile(":")

class BlockComment(Token):
    PATTERN = re.compile("/\\*(.*?)\\*/", re.DOTALL)

    def __init__(self, match_data, line_number):
        super(BlockComment, self).__init__(match_data.group(1), line_number)

class InlineComment(Token):
    PATTERN = re.compile("//(.*)")

    def __init__(self, match_data, line_number):
        super(InlineComment, self).__init__(match_data.group(1), line_number)

class Number(Token):
    PATTERN = re.compile("(-?[0-9]+(?:\\.[0-9]+)?)")

class ParameterSeperator(Token):
    PATTERN = re.compile(" *,")

class Identifier(Token):
    PATTERN = re.compile("((?:(?:[A-Z]|[_])+[0-9]*)+(?:::(?:(?:[A-Z]|[_])+(?:[0-9])*)+)*\\$?)", re.IGNORECASE)

class GlobalReference(Token):
    PATTERN = re.compile("\\$(\w+(?:::\w+)*)")

    def __init__(self, match_data, line_number):
        super(GlobalReference, self).__init__(match_data.group(1), line_number)

class LocalReference(Token):
    PATTERN = re.compile("%(\w+)")

    def __init__(self, match_data, line_number):
        super(LocalReference, self).__init__(match_data.group(1), line_number)

def build_operator_regex():
    """
        A helper routine to generate the necessary regex patterns for matching operators so that we don't have to write out the
        entire large sequence by hand.
    """
    assignment_operators = ["=", "\\+", "-", "\\*", "!", "<", ">", "&", "\\|", "%", "~", "/"]
    nonassignment_operators = ["@", "TAB", "SPC", "\\$=", "\\|\\|", "\\&\\&", "\\^"] + assignment_operators
    assignment_operators = ["(?:%s=)" % operator for operator in assignment_operators]

    built_result = "(%s){1}" % "|".join(assignment_operators + nonassignment_operators)
    return re.compile(built_result)

class Operator(Token):
    PATTERN = build_operator_regex()

class String(Token):
    PATTERN = re.compile("(\"|')(.+?)(?<!\\\\)\\1")

    def __init__(self, match_data, line_number):
        super(String, self).__init__(match_data.group(2), line_number)

class Terminator(Token):
    PATTERN = re.compile(" *;")

class WhiteSpace(Token):
    PATTERN = re.compile("\s+")

class ParenthesesOpen(Token):
    PATTERN = re.compile("\\(")

class ParenthesesClose(Token):
    PATTERN = re.compile("\\)")

class BlockOpen(Token):
    PATTERN = re.compile("{")

class QuestionMark(Token):
    PATTERN = re.compile("\\?")

class BlockClose(Token):
    PATTERN = re.compile("}")

class AttributeAccessor(Token):
    PATTERN = re.compile("\\.")

def generate_token_stream(buffer, ignore_whitespace=False):
    current_line_number = 1
    while len(buffer) != 0:
        produced_match = False
        for token_type in Token.__subclasses__():
            match_data = re.match(token_type.PATTERN, buffer)

            if match_data is not None:
                produced_match = True
                current_line_number += len(re.findall("(?:\r\n)|\n", buffer[0:match_data.end()]))

                if token_type is not WhiteSpace or ignore_whitespace is False:
                    yield token_type(match_data, current_line_number)
                buffer = buffer[match_data.end():]

        if produced_match is False and len(buffer) != 0:
            print(buffer[0:100])
            raise LexicalError("!!! Failed to match next token!")

if __name__ == "__main__":
    with open(sys.argv[1], "r") as handle:
        with open("lexout.txt", "w") as writer:
            for token_data in generate_token_stream(handle.read()):
                writer.write(str(token_data) + "\n")
