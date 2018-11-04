from __future__ import print_function
import re

###### Lexer

class Token(object):
    def __init__(self, type=None, value=None):
        self.type = type
        self.value = value


def tokenizer(input):
    current = 0
    tokens = []
    while current < len(input):
        char = input[current]
        if char == '(':
            token = {
                'type': 'paren',
                'value': '('
            }
            tokens.append(token)
            current += 1
            continue
        if (char == ')'):
            token = {
                'type': 'paren',
                'value': ')'
            }
            tokens.append(token)
            current += 1
            continue

        # Eat up white spaces
        WHITESPACE = r'\s'
        p = re.compile(WHITESPACE)
        if p.match(char):
            current += 1
            continue

        # Accumulate digits until it sees something else
        NUMBERS = r'[0-9]'
        p = re.compile(NUMBERS)
        if p.match(char):
            value = ''
            while (p.match(char)):
                value += char
                current += 1
                char = input[current]
            token = {
                'type': 'number',
                'value': value
            }
            tokens.append(token)
            continue

        # Opening and closing of a string
        if char == '"':
            value = ''
            current += 1
            char = input[current]
            while (char != '"'):
                value += char
                current += 1
                char = input[current]
            current += 1
            char = input[current]
            token = {
                'type': 'string',
                'value': value
            }
            tokens.append(token)
            continue

        # Identifier
        LETTERS = r'[a-z]'
        p = re.compile(LETTERS)
        if p.match(char):
            value = ''
            while p.match(char):
                value += char
                current += 1
                char = input[current]
            token = {
                'type': 'name',
                'value': value
            }
            tokens.append(token)
            continue

        raise Exception('I dont know what this character is: ' + char)
    return tokens


##### Parser

def parser(tokens):

    class nonlocal: pass
    nonlocal.current = 0

    def walk():
        token = tokens[nonlocal.current]
        if token['type'] == 'number':
            nonlocal.current += 1
            return {
                'type': 'NumberLiteral',
                'value': token['value']
            }
        if token['type'] == 'string':
            nonlocal.current += 1
            return {
                'type': 'StringLiteral',
                'value': token['value']
            }
        if token['type'] == 'paren' and token['value'] == '(':
            # skip opening paren
            nonlocal.current += 1
            token = tokens[nonlocal.current]
            node = {
                'type': 'CallExpression',
                'name': token['value'],
                'params': []
            }

            nonlocal.current += 1
            token = tokens[nonlocal.current]

            while (token['type'] != 'paren') or (token['type'] == 'paren' and token['value'] != ')'):
                node['params'].append(walk())
                token = tokens[nonlocal.current]

            nonlocal.current += 1
            return node

        raise Exception(token['type'])

    ast = {
        'type': 'Program',
        'body': []
    }

    while nonlocal.current < len(tokens):
        ast['body'].append(walk())

    return ast

def traverser(ast, visitor):
    class nonlocal: pass
    nonlocal.visitor = visitor

    def traverse_array(array, parent):
        for child in array:
            print('child {}'.format(child))
            traverse_node(child, parent)

    def traverse_node(node, parent):
        methods = nonlocal.visitor.get(node.get('type'))

        if methods and methods['enter']:
            methods['enter'](node, parent)

        node_type = node['type']

        if node_type == 'Program':
            traverse_array(node['body'], node)
        elif node_type == 'CallExpression':
            traverse_array(node['params'], node)
        elif node_type == 'NumberLiteral' or node_type == 'StringLiteral':
            print('Just the end')

        else:
            raise Exception(node['type'])

        if methods and methods.get('exit'):
            methods['exit'](node, parent)

    traverse_node(ast, None)

def transformer(ast):

    # Create a `new_ast` which like our previous AST will have a program node.
    new_ast = {
        'type': 'Program',
        'body': []
    }

    # A hack to push nodes to the parent's context
    ast['_ctx'] = new_ast['body']

    def string_enter(node, parent):
        parent['_ctx'].append({
            'type': 'StringLiteral',
            'value': node['value']
        })

    def num_enter(node, parent):
        parent['_ctx'].append({
            'type': 'NumberLiteral',
            'value': node['value']
        })

    def call_expr_enter(node, parent):
        expression = {
            'type': 'CallExpression',
            'callee': {
                'type': 'Identifier',
                'name': node['name']
            },
            'arguments': []
        }
        node['_ctx'] = expression['arguments']
        if parent['type'] != 'CallExpression':
            expression = {
                'type': 'ExpressionStatement',
                'expression': expression
            }

        parent['_ctx'].append(expression)

    # visitor = {
    #     'NumberLiteral': {
    #         'enter': num_enter
    #     },
    #     'StringLiteral': {
    #         'enter': string_enter
    #     },
    #     'CallExpression': {
    #         'enter': call_expr_enter
    #     }
    # }
    traverser(ast, {
        'NumberLiteral': {
            'enter': num_enter
        },
        'StringLiteral': {
            'enter': string_enter
        },
        'CallExpression': {
            'enter': call_expr_enter
        }
    })

    return new_ast

def code_generator(node):
    node_type = node['type']
    if node_type == 'Program':
        return '\n'.join(map(code_generator, node['body']))
    elif node_type == 'ExpressionStatement':
        return code_generator(node['expression']) + ';'
    elif node_type == 'CallExpression':
        return code_generator(node['callee']) + \
            '(' + \
            ', '.join(map(code_generator, node['arguments'])) + \
            ')'

    elif node_type == 'Identifier':
        return node['name']

    elif node_type == 'NumberLiteral':
        return node['value']

    elif node_type == 'StringLiteral':
        return '"' + node['value'] + '"'
    else:
        raise Exception(node['type'])


def compiler(input):
    tokens  = tokenizer(input)
    ast     = parser(tokens)
    new_ast = transformer(ast)
    output  = code_generator(new_ast)

    return output
