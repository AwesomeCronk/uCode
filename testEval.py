import sys

# a&b = a AND b
# a^b = a XOR b
# a|b = a OR b
# !a = NOT a


def findChunk(source):
    depth = 1
    i = 0
    char = source[i]

    # Seek to first `(`
    while char != '(':
        i += 1
        char = source[i]

    beg = i
    
    while depth != 0:
        i += 1
        char = source[i]
        if char == '(': depth += 1
        elif char == ')': depth -= 1

    end = i

    return beg, end

def evaluatePrecedence(source, recursiveness=0):
    if '(' in source:
        beg, end = findChunk(source)
        print('  ' * recursiveness, beg, end)
        source = source[:beg] + evaluatePrecedence(source[beg+1:end], recursiveness+1) + source[end+1:]

    if '|' in source:
        chunks = [evaluatePrecedence(chunk) for chunk in source.split('|')]
        # OR the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            chunks[0] = str(int(chunks[0]) | int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif '^' in source:
        chunks = [evaluatePrecedence(chunk) for chunk in source.split('^')]
        # XOR the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            chunks[0] = str(int(chunks[0]) ^ int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif '&' in source:
        chunks = [evaluatePrecedence(chunk) for chunk in source.split('&')]
        # AND the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            chunks[0] = str(int(chunks[0]) & int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif source[0] == '!':
        chunk = evaluatePrecedence(source[1:])
        if chunk == '0': return '1'
        else: return '0'

    


def evaluateLeftRight(source, recursiveness=0):
    a = ''
    b = ''
    op = ''

    print(('  ' * recursiveness) + 'source: {}'.format(source))

    if source[0] in '01':
        # `source[0]` is a `source[1]` is `op`; `source[2:]` is `b`
        a = source[0]
        op = source[1]
        if source[2] == '(':
            b = evaluateLeftRight(source[3:-1], recursiveness + 1)
        else:
            b = source[2]

    elif source[0] == '!':
        # `source[1:]` is `a`; `op` is "!"; `b` is ""
        raise NotImplementedError('We don\'t support "!" yet')

    elif source[0] == '(':
        # Cycle through `source` until the matching ")" is found; `a` is `evaluateLeftRight(<that mess>)`
        index = 0
        blockDepth = 1
        while blockDepth > 0:
            index += 1
            if source[index] == '(': blockDepth += 1
            elif source[index] == ')': blockDepth -= 1
        # `index` points to closing parenthesis
        
        a = evaluateLeftRight(source[1:index], recursiveness + 1)
        op = source[index + 1]
        if source[index + 2] == '(':
            b = evaluateLeftRight(source[3:-1], recursiveness + 1)
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
    
print(evaluateLeftRight(sys.argv[1]))

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
#     print(evaluateLeftRight(source))
