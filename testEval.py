import sys

# a&b = a AND b
# a^b = a XOR b
# a|b = a OR b
# !a = NOT a

def evaluate(source, recursiveness=0):
    if source in ('0', '1'): return source

    print('| ' * recursiveness + ',-Source: {}'.format(source))

    # Isolate contents of parenthesis blocks
    while '(' in source or ')' in source:
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
        print('| ' * recursiveness + '|-Parentheses {} thru {}'.format(beg, end))

        source = source[:beg] + evaluate(source[beg+1:end], recursiveness+1) + source[end+1:]

    if '|' in source:
        chunks = [evaluate(chunk, recursiveness+1) for chunk in source.split('|')]
        # OR the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            print('| ' * recursiveness + '`-{} OR {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) | int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif '^' in source:
        chunks = [evaluate(chunk, recursiveness+1) for chunk in source.split('^')]
        # XOR the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            print('| ' * recursiveness + '`-{} XOR {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) ^ int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif '&' in source:
        chunks = [evaluate(chunk, recursiveness+1) for chunk in source.split('&')]
        # AND the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            print('| ' * recursiveness + '`-{} AND {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) & int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif source[0] == '!':
        chunk = evaluate(source[1:], recursiveness+1)
        print('| ' * recursiveness + '`-NOT {}'.format(chunk))
        if chunk == '0': return '1'
        else: return '0'
    
    else: return source


def verify(source, names):
    specialChars = '!&^|()'

    # No special characters in names
    for name in names:
        for char in specialChars:
            if char in name:
                print('Invalid name: "{}"'.format(name))
                return False

    # Split source by all names
    pieces = [source]
    for name in names:
        for p, piece in enumerate(pieces):
            if name in piece:
                splitPiece = piece.split(name)
                splitPiece.reverse()
                del pieces[p]
                for smallerPiece in splitPiece:
                    pieces.insert(p, smallerPiece)
    print(pieces)

    # Remove empty bits at ends, they result from names occuring at the ends of source
    if pieces[0] == '': del pieces[0]
    if pieces[-1] == '': del pieces[-1]

    # No names next to each other
    if '' in pieces:
        print('Cannot put two names next to each other')
        return False
    
    # No non-special characters except for names
    for piece in pieces:
        for char in piece:
            if not char in specialChars:
                print('Character "{}" not part of a name is invalid'.format(char))
                return False

    # Matching parentheses
    # if source.count('(') != source.count(')'):
    #     print('Mismatched parenthesis count')
    # This method cannot detect out-of-order parentheses that have acceptable count

    # Matching parentheses
    depth = 0
    for c, char in enumerate(source):
        if char == '(': depth += 1
        if char == ')': depth -= 1
        if depth < 0:
            print('")" at {} has no matching "("'.format(c))
            return False
    if depth != 0:
        print('"(" has no matching ")" at end')
        return False

    return True


if __name__ == '__main__':
    source = sys.argv[1]
    names = ['A', 'B', 'C']

    if verify(source, names):
        for i in range(2 ** len(names)):
            evaluatable = source
            bits = list(bin(i)[2:].zfill(len(names)))
            for n, name in enumerate(names):
                evaluatable = evaluatable.replace(name, bits[n])
            print(evaluatable)
            print(evaluate(evaluatable))

    # print(evaluate(sys.argv[1]))
