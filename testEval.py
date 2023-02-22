import sys

# a&b = a AND b
# a|b = a OR b
# a^b = a XOR b
# !a = NOT a

def evaluate(source, recursiveness=0):
    a = ''
    b = ''
    op = ''

    print(('  ' * recursiveness) + 'source: {}'.format(source))

    if source[0] in '01':
        # `source[0]` is a `source[1]` is `op`; `source[2:]` is `b`
        a = source[0]
        op = source[1]
        if source[2] == '(':
            b = evaluate(source[3:-1], recursiveness + 1)
        else:
            b = source[2]

    elif source[0] == '!':
        # `source[1:]` is `a`; `op` is "!"; `b` is ""
        raise NotImplementedError('We don\'t support "!" yet')

    elif source[0] == '(':
        # Cycle through `source` until the matching ")" is found; `a` is `evaluate(<that mess>)`
        index = 0
        blockDepth = 1
        while blockDepth > 0:
            index += 1
            if source[index] == '(': blockDepth += 1
            elif source[index] == ')': blockDepth -= 1
        # `index` points to closing parenthesis
        
        a = evaluate(source[1:index], recursiveness + 1)
        op = source[index + 1]
        if source[index + 2] == '(':
            b = evaluate(source[3:-1], recursiveness + 1)
        else:
            b = source[2]

    else:
        raise ValueError('Unexpected token "{}" at start of expression'.format(source[0]))
    
    print(('  ' * recursiveness) + 'a: {} b: {} op: {}'.format(a, b, op))
    
    if op == '&':
        result = a if a == b else '0'
    elif op == '|':
        result = '1' if a == '1' or b == '1' else '0'
    elif op == '^':
        result = '1' if (a == '1' or b == '1') and a != b else '0'
    elif op == '!':
        result = '1' if a == '0' else '0'

    print('  ' * recursiveness + 'result: {}'.format(result))
    return result
    
print(evaluate(sys.argv[1]))

# lines = ['a', 'b', 'c']
# 
# for condition in range(2 ** len(lines)):
#     source = sys.argv[1].replace(' ', '')
# 
#     # Replace line names with values
#     for l, line in enumerate(lines):
#         value = (condition & (1 << (len(lines) - l - 1))) >> (len(lines) - l - 1)  # Extracts a 0 or 1 from `condition`
#         source = source.replace(line, str(value))
#     
#     print(source)
# 
#     print(evaluate(source))
