import sys
import collections

import tslexer

class ParserError(StandardError):
    """
        A class representing a parse error of some form.
    """

class SyntaxError(ParserError):
    """
        Input is syntactically incorrect.
    """

    def __init__(self, input_token, expected=None, message=None):
        # Ensure the expected parameter is always a list
        if type(expected) is not list:
            expected = [expected]

        output_message = "Syntax error on line %s. " % (input_token.line_number if input_token is not None else "(EOF)")
        if expected is not None:
            expected = ", ".join([expected_type.__name__ if expected_type is not str else expected_type for expected_type in expected ])
            expected = "Expected: %s. Got: %s %s" % (expected, input_token.__class__.__name__ if input_token is not None else "(EOF)", repr(input_token.data) if input_token is not None else "(EOF)")
            output_message += expected

        if message is not None:
            output_message += " (%s)" % message

        super(SyntaxError, self).__init__(output_message)

class ASTElement(object):
    commenting = None
    """
         A list of comments associated with this AST element.
    """

    def __init__(self, commenting=None):
        self.commenting = commenting

class ObjectInstantiation(ASTElement):
    def __init__(self, type, name, attribute_map, children=None, commenting=None):
        super(ObjectInstantiation, self).__init__(commenting=commenting)

        self.type = type
        self.name = name
        self.children = children
        self.attribute_map = attribute_map

    def __repr__(self):
        name = "No Name" if self.name is None else self.name
        return """
        %s
        <Creating new %s ('%s'):
        %s
        >
        """ % (("/*\n%s\n*/" % "\n".join(self.commenting) if len(self.commenting) != 0 else ""), self.type, self.name, "\n".join(["%s=%s" % (attribute_name, attribute_value) for attribute_name, attribute_value in zip(self.attribute_map.keys(), self.attribute_map.values())]))

class GlobalAssignment(ASTElement):
    name = None
    """
        The name given to this global.
    """

    value = None
    """
        The value given to this global.
    """

    def __init__(self, name, value, array_indexes=None, commenting=None):
        super(GlobalAssignment, self).__init__(commenting=commenting)

        self.name = name
        self.value = value
        self.array_indexes = array_indexes

class GlobalReference(ASTElement):
    name = None
    """
        The name given to this global.
    """

    array_indexes = None

    def __init__(self, name, array_indexes=None):
        super(GlobalReference, self).__init__()
        self.name = name
        self.array_indexes = array_indexes

class FunctionCall(ASTElement):
    name = None
    """
        The name of the function being called.
    """

    parameters = None
    """
        Parameters being passed to this function.
    """

    def __init__(self, name, parameters=None):
        super(FunctionCall, self).__init__()
        self.name = name
        self.parameters = parameters

class AST(object):
    current_enclosure = None
    """
        The current enclosing structure.
    """

    current_comments = None
    """
        A buffer of all comments leading up to the next significant token.
    """

    def handle_comment_tokens(self, input_token, token_stream):
        self.current_comments.append(input_token.data)

    def decode_global_reference(self, input_token, token_stream):
        global_name = input_token.data

        next_token = next(token_stream)
        array_indexes = []
        if type(next_token) is tslexer.ArrayOpen:
            array_indexes = self.decode_parameters(next(token_stream), token_stream)
        return GlobalReference(name=global_name)

    def decode_function_call(self, input_token, token_stream):
        """
            Decodes a function call from the token stream.

            :param input_token: The identifier representing the name of the function to call.
            :param token_stream: The token stream to pull from.
        """

        function_name = input_token.data

        # Expect a parentheses open
        next_token = next(token_stream)
        if type(next_token) is not tslexer.ParenthesesOpen:
            raise SyntaxError(next_token, expected=tslexer.ParenthesesOpen)
        return FunctionCall(function_name, self.decode_parameters(next(token_stream), token_stream))

    def decode_parameters(self, input_token, token_stream):
        """
            Decodes parameters for either an array or a function call. This will return all tokens ending at the first closing parentheses
            or closing array.

            FIXME: This fails in a case like: $a[$abc[5,6,7], 5, 1, $obs] = 1;
            OR: $a[$abc[5,6,7], 5, $abc[$myabc[5,6,7], 9]] = 1;
            This is caused by the internal global popping off the outer ] token.

            :param input_token: The first token to be considered part of the parameters.
            :param token_stream: The stream of tokens to use for this.
        """

        parameter_data = []
        if type(input_token) is not tslexer.ParenthesesClose:
            parameter_data.append(input_token)
        else:
            return parameter_data

        next_token = input_token
        while type(next_token) is not tslexer.ParenthesesClose:
            next_token = next(token_stream)

            expected_tokens = [tslexer.ArrayClose, tslexer.ParenthesesClose, tslexer.String, tslexer.GlobalReference, tslexer.Number, tslexer.ParameterSeperator]
            if type(next_token) not in expected_tokens:
                raise SyntaxError(next_token, expected=expected_tokens)

            if type(next_token) is tslexer.ParameterSeperator:
                continue
            elif type(next_token) is tslexer.ArrayClose or type(next_token) is tslexer.ParenthesesClose:
                return parameter_data
            elif type(next_token) is tslexer.GlobalReference:
                parameter_data.append(self.decode_global_reference(next_token, token_stream))
            elif type(next_token) is tslexer.Identifier:
                parameter_data.append(self.decode_function_call(next_token, token_stream))
            else:
                parameter_data.append(next_token)
        return parameter_data

    def handle_global_tokens(self, input_token, token_stream, rvalue=False):
        global_name = input_token.data

        def process_global(input_token, token_stream, rvalue=False):
            # We can have an assignment or a array open here
            expected_tokens = [tslexer.Operator, tslexer.ArrayOpen]
            next_token = next(token_stream)

            if type(next_token) not in expected_tokens:
                raise SyntaxError(next_token, expected=expected_tokens)

            array_indexes = []
            if type(next_token) is tslexer.ArrayOpen:
                while type(next_token) is not tslexer.ArrayClose:
                    next_token = next(token_stream)

                    expected_tokens = [tslexer.ArrayClose, tslexer.String, tslexer.GlobalReference, tslexer.Number, tslexer.ParameterSeperator]
                    if type(next_token) not in expected_tokens:
                        raise SyntaxError(next_token, expected=expected_tokens)

                    if type(next_token) is tslexer.ParameterSeperator:
                        continue
                    elif type(next_token) is tslexer.ArrayClose:
                        next_token = next(token_stream)
                        break
                    elif type(next_token) is tslexer.GlobalReference:
                        array_indexes.append(self.decode_global_reference(next_token, token_stream))
                    else:
                        array_indexes.append(next_token.data)

            # Next should be an equals operator unless we're inline.
            if rvalue is False and type(next_token) is not tslexer.Operator and next_token.data != "=":
                raise SyntaxError(next_token, expected=[tslexer.Operator], message="Should be =.")

            # We can process new values, strings, numbers or global references here.
            expected_tokens = [tslexer.String, tslexer.Number, tslexer.GlobalReference, tslexer.Identifier]
            next_token = next(token_stream)

            if type(next_token) not in expected_tokens:
                raise SyntaxError(next_token, expected=expected_tokens)

            current_result = None
            if type(next_token) is tslexer.GlobalReference:
                current_result = self.decode_global_reference(next_token, token_stream)
            elif type(next_token) is tslexer.Number or type(next_token) is tslexer.String:
                current_result = GlobalAssignment(name=global_name, value=next_token, array_indexes=array_indexes)
            elif type(next_token) is tslexer.Identifier:
                current_result = self.decode_function_call(next_token, token_stream)

            # Handle the terminator.
            if rvalue is False:
                next_token = next(token_stream)
                if type(next_token) is not tslexer.Terminator:
                    raise SyntaxError(next_token, expected=tslexer.Terminator)

        return process_global(input_token, token_stream)

    def handle_new_keyword(self, input_token, token_stream, rvalue=False):
        """
            The next series of tokens are going to be related to instantiating a new object.
        """

        def process_new_keyword(input_token, token_stream, rvalue=False):
            # The next token should always be an identifier here.
            identifier_token = next(token_stream)
            if type(identifier_token) is not tslexer.Identifier:
                raise SyntaxError(identifier_token, expected=[tslexer.Identifier])

            instance_name = None
            children_instances = []
            instance_type = identifier_token.data

            # Optionally 0we can provide parentheses if we want to name this object
            next_token = next(token_stream)
            if type(next_token) is tslexer.ParenthesesOpen:
                identifier_token = next(token_stream)

                expected_tokens = [tslexer.Identifier, tslexer.ParenthesesClose]
                if type(identifier_token) not in expected_tokens:
                    raise SyntaxError(identifier_token, expected=[tslexer.Identifier])

                if type(identifier_token) is not tslexer.ParenthesesClose:
                    instance_name = identifier_token.data

                    closing_parentheses = next(token_stream)
                    if type(closing_parentheses) is not tslexer.ParenthesesClose:
                        raise SyntaxError(closing_parentheses, expected=[tslexer.ParenthesesClose])

            opening_block = next(token_stream)
            if type(opening_block) is not tslexer.BlockOpen:
                raise SyntaxError(opening_block, expected=[tslexer.BlockOpen])

            attribute_map = collections.OrderedDict()

            # Everything in between here is attributes but we may call functions or inline instantiate something here
            current_identifier_name = None
            finished_consuming = False
            for current_token in token_stream:
                if type(current_token) is tslexer.BlockClose:
                    finished_consuming = True
                    break

                # Load an identifier if one isn't loaded already
                if current_identifier_name is None:
                    expected_tokens = [tslexer.Identifier, tslexer.InlineComment, tslexer.BlockComment]
                    if type(current_token) not in expected_tokens:
                        raise SyntaxError(current_token, expected=expected_tokens)
                    elif type(current_token) is tslexer.InlineComment or type(current_token) is tslexer.BlockComment:
                        self.handle_comment_tokens(current_token, token_stream)
                    else:
                        current_identifier_name = current_token.data

                        if current_identifier_name == "new":
                            children_instances.append(process_new_keyword(current_token, token_stream, rvalue=False))
                            current_identifier_name = None
                            continue
                else:
                    expected_tokens = [tslexer.Operator, tslexer.ArrayOpen]
                    if type(current_token) not in expected_tokens or (type(current_token) is tslexer.Operator and current_token.data != "="):
                        raise SyntaxError(current_token, expected=expected_tokens, message="Should be =.")

                    array_indexes = []
                    if type(current_token) is tslexer.ArrayOpen:
                        # We can have digits or strings as elements ib attributes
                        expected_tokens = [tslexer.ArrayClose, tslexer.Number, tslexer.String, tslexer.ParameterSeperator]

                        while type(current_token) is not tslexer.ArrayClose:
                            current_token = next(token_stream)
                            if type(current_token) not in expected_tokens:
                                raise SyntaxError(current_token, expected=expected_tokens)

                            if type(current_token) is not tslexer.ArrayClose and type(current_token) is not tslexer.ParameterSeperator:
                                array_indexes.append(current_token.data)

                        # Read the next token which should be an equals
                        current_token = next(token_stream)

                    # Collision on attribute assignment without array indexes
                    if len(array_indexes) == 0 and current_identifier_name in attribute_map:
                        raise SyntaxError(current_token, message="Duplicate attribute assignment! (Assigned attribute '%s' at least twice.)" % current_identifier_name)

                    expected_tokens = [tslexer.Operator]
                    if type(current_token) not in expected_tokens or (type(current_token) is tslexer.Operator and current_token.data != "="):
                        raise SyntaxError(current_token, expected=expected_tokens, message="Should be =.")

                    # Read the beginning of the payload that we're assigning
                    attribute_payload_token = next(token_stream)

                    if type(attribute_payload_token) is tslexer.Identifier and attribute_payload_token.data in self.identifier_handlers:
                        # Only new is valid here
                        if attribute_payload_token.data == "new":
                            attribute_map[current_identifier_name] = process_new_keyword(attribute_payload_token, token_stream, rvalue=True)
                        else:
                            raise SyntaxError(attribute_payload_token, expected=[tslexer.Identifier], message="Keyword '%s' not valid here." % attribute_payload_token.data)
                    else:
                        if len(array_indexes) == 0:
                            attribute_map[current_identifier_name] = attribute_payload_token
                        else:
                            current_key = current_identifier_name
                            current_map = attribute_map

                            # Collision on attribute name with array indexes
                            diverted_keys = False
                            for index, array_index in enumerate(array_indexes):
                                if index != len(array_indexes) - 1:
                                    if current_key not in current_map:
                                        diverted_keys = True
                                        current_map[current_key] = {array_index: {}}

                                    current_map = current_map[current_key]
                                    current_key = array_index
                                else:
                                    current_key = array_indexes[-1]
                                    if diverted_keys is False and current_key in current_map:
                                        array_indexes = ", ".join([repr(array_index) for array_index in array_indexes])
                                        raise SyntaxError(current_token, message="Duplicate attribute assignment! (Assigned attribute '%s' at least twice with array indexes %s)" % (current_identifier_name, array_indexes))

                                    current_map[current_key] = attribute_payload_token

                    # The attribute should be headed off with a terminator at some point.
                    terminator_token = next(token_stream)
                    if type(terminator_token) is not tslexer.Terminator:
                        raise SyntaxError(terminator_token, expected=[tslexer.Terminator])
                    current_identifier_name = None

            if finished_consuming is False:
                raise SyntaxError(None, expected=[tslexer.BlockClose])

            if rvalue is False:
                terminator = next(token_stream)
                if type(terminator) is not tslexer.Terminator:
                    raise SyntaxError(terminator, expected=[tslexer.Terminator])

            # Combine all the loaded data into an instance and return it
            comment_data = self.current_comments
            self.current_comments = []
            return ObjectInstantiation(name=instance_name, children=children_instances, type=instance_type, attribute_map=attribute_map, commenting=comment_data)

        # Actually run the subroutine
        return process_new_keyword(input_token, token_stream, rvalue)

    identifier_handlers = {
        "function": None,
        "new": handle_new_keyword,
    }

    def handle_identifier_tokens(self, input_token, token_stream):
        """
            Handles identifier tokens. These can either be true identifiers or reserved keywords.
        """

        identifier_name = input_token.data
        if identifier_name in self.identifier_handlers:
            return self.identifier_handlers[identifier_name](self, input_token, token_stream)

    token_handlers = {
        tslexer.InlineComment: handle_comment_tokens,
        tslexer.Identifier: handle_identifier_tokens,
        tslexer.BlockComment: handle_comment_tokens,
        tslexer.GlobalReference: handle_global_tokens,
    }

    root_data = None

    def __init__(self, input):
        self.current_comments = []
        self.root_data = self.parse(input)

    def parse(self, input):
        if type(input) is str:
            input = tslexer.generate_token_stream(input, ignore_whitespace=True)

        result = []
        for token in input:
            if type(token) not in self.token_handlers:
                raise ParserError("!!! No handler for token type: '%s'" % token.__class__.__name__)
            current_result = self.token_handlers[type(token)](self, token, input)
            if current_result is not None:
                result.append(current_result)
        return result

if __name__ == "__main__":
    with open(sys.argv[1], "r") as handle:
        result = AST(handle.read())

        with open("out.txt", "w") as writer:
            def recurse_test(input, current_depth):
                spacing = "".join(["    "] * current_depth)
                for current_element in input:
                    line_data = str(current_element).split("\n")
                    line_data = "\n".join(["%s%s" % (spacing, current_line.lstrip()) for current_line in line_data])
                    writer.write(line_data + "\n")

                for current_element in input:
                    if type(current_element) is ObjectInstantiation:
                        recurse_test(current_element.children, current_depth + 1)

            recurse_test(result.root_data, 0)
