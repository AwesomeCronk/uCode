import argparse, json5

_version = '1.0.0'

def getArgs():
    parser = argparse.ArgumentParser('uCode', description='v{}; Generates microcode ROM binaries. See https://github.com/AwesomeCronk/uCode for more information.'.format(_version))
    parser.add_argument(
        'infile',
        help='File to read JSON5 ucode description from'
    )
    parser.add_argument(
        '-o',
        '--outfile',
        help='File to write ucode binary to',
        default='ucode.bin'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='Set output verbosity',
        type=int,
        default=0
    )

    return parser.parse_args()


def verifyCondition(source, names):
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
    # print('Pieces:', pieces)

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

def evaluateCondition(source, recursiveness=0):

    # a&b = a AND b
    # a^b = a XOR b
    # a|b = a OR b
    # !a = NOT a
    
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

        source = source[:beg] + evaluateCondition(source[beg+1:end], recursiveness+1) + source[end+1:]

    if '|' in source:
        chunks = [evaluateCondition(chunk, recursiveness+1) for chunk in source.split('|')]
        # OR the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            print('| ' * recursiveness + '`-{} OR {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) | int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif '^' in source:
        chunks = [evaluateCondition(chunk, recursiveness+1) for chunk in source.split('^')]
        # XOR the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            print('| ' * recursiveness + '`-{} XOR {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) ^ int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif '&' in source:
        chunks = [evaluateCondition(chunk, recursiveness+1) for chunk in source.split('&')]
        # AND the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            print('| ' * recursiveness + '`-{} AND {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) & int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif source[0] == '!':
        chunk = evaluateCondition(source[1:], recursiveness+1)
        print('| ' * recursiveness + '`-NOT {}'.format(chunk))
        if chunk == '0': return '1'
        else: return '0'
    
    else: return source


def encodeStep(step):
    bits = [0] * len(controlLines)

    # Easier way of doing a Set_State operation
    # Requires that State_Set and State_0..State_# be available
    if len(step) == 1 and step[0][0:11] == 'State_Set>>':
        # print('Quick state change')
        stateName = step[0][11:]
        stateNum = states.index(stateName)
        binStr = bin(stateNum)[2:].zfill(len(bin(numStates)[2:]))
        # Python uses bit 0 as MSB, Digital uses bit 0 as LSB, have to convert
        stateLines = ['State_Set']
        for i in range(len(binStr)):
            if binStr[-i - 1] == '1': stateLines.append('State_' + str(i))
        for line in stateLines: bits[len(controlLines) - controlLines.index(line) - 1] = 1

    # Normal step encoding
    else:
        for line in step: bits[len(controlLines) - controlLines.index(line) - 1] = 1

    # Convert bits to bytes and return
    intValue = 0
    for bit in bits: intValue *= 2; intValue += bit
    return int.to_bytes(intValue, len(controlLines) // 8, 'big')


if __name__ == '__main__':
    args = getArgs()
    print('uCode {}'.format(_version))

    with open(args.infile, 'r') as jsonFile: json = json5.load(jsonFile)

    numControls     = json['numControls']
    numConditions   = json['numConditions']
    numStates       = json['numStates']
    numSteps        = json['numSteps']
    controlLines    = json['controlLines']
    conditionLines  = json['conditionLines']
    states          = json['states']
    stateOrder      = json['stateOrder']

    # Verification of line, condition, state, and step counts
    if len(controlLines) != numControls: print('Line count {} does not match provided values'.format(len(controlLines))); exit(1)
    if len(controlLines) % 8 != 0: print('Line count {} must be a multiple of 8'.format(len(controlLines))); exit(1)
    if len(conditionLines) != numConditions: print('Condition count {} does not match provided values'.format(len(conditionLines))); exit(1)
    if len(stateOrder) != numStates: print('State order count {} does not match provided values'.format(len(stateOrder))); exit(1)
    for s, stateName in enumerate(stateOrder):  # `s` is state name, `state` is state contents
        if len(states[stateName]) > numSteps and s in stateOrder:
            print('Too many steps ({}) for state {}'.format(len(states[stateName]), s)); exit(1)

    # Encode the steps of each state
    binary = b''
    for stateName in stateOrder:
        state = states[stateName]
        if args.verbose >= 1: print('State {}:'.format(stateName))

        # Allows states to leave off any steps which need not be specified
        # If a state needs less steps than specified, it can define only what it needs and the rest will be filled in
        while len(states[stateName]) < numSteps:
            try: states[stateName].append(json['defaultStep'])
            except IndexError: print('Not all steps defined in state {} but defaultStep is not defined'.format(stateName)); exit(1)

        for s, step in enumerate(states[stateName]):
            if args.verbose >= 2: print('  Step {}: '.format(s), end='')

            # Steps can be a list of control lines and be constant
            if isinstance(step, list):
                if len(step) == 0:
                    if args.verbose >= 2: print('blank')
                    binary = binary + b'\x00' * ((len(controlLines) // 8) * (2 ** numConditions))

                else:
                    if args.verbose >= 2: print('constant')
                    for k in range(2 ** numConditions):
                        binary = binary + encodeStep(step)

            # Or can be a dict of conditions and outputs and be conditional
            elif isinstance(step, dict):
                if args.verbose >= 2: print('conditional')
                validCases = [[None] * len(step) for _ in range(2 ** numConditions)]    # List of lists; indexed by case number, sublists indexed by condition number

                for i0, condition in enumerate(step.keys()):
                    print('    Condition: "{}"'.format(condition))
                    if condition != '':
                        if not verifyCondition(condition, conditionLines): exit(1)  # `verifyCondition` will print the reason

                        for i1 in range(2 ** numConditions):
                            evaluatable = condition
                            bits = list(bin(i1)[2:].zfill(len(conditionLines)))
                            # print('Bits:', bits)
                            for i2, conditionLine in enumerate(conditionLines):
                                evaluatable = evaluatable.replace(conditionLine, bits[i2])
                            
                            validCases[i1][i0] = evaluateCondition(evaluatable) == '1'
                
                # print('    Valid cases:')
                # for i in validCases: print('    {}'.format(i))

                lines = list(step.values())
                print('    Lines: {}'.format(lines))

                for i0, case in enumerate(validCases):
                    # print('    Case: {}, Matches: {}'.format(case, case.count(True)))
                    
                    if case.count(True) == 1:
                        print('    Chose: {}'.format(lines[case.index(True)]))
                        binary = binary + encodeStep(lines[case.index(True)])

                    elif case.count(True) == 0:
                        print('    Chose: {}'.format(lines[case.index(None)]))
                        binary = binary + encodeStep(lines[case.index(None)])

                    else:
                        matchingConditions = []
                        for i1, match in enumerate(case):
                            if match:
                                matchingConditions.append(step.keys()[i1])

                        print('Case {} matches multiple conditions: "{}"'.format(bin(i0)[2:], '", "'.join(matchingConditions)))
            
            else:
                print('Step {} must be of type list or dict'.format(s)); exit(1)

    with open(args.outfile, 'wb') as file: file.write(binary)
    print('Wrote binary to {}'.format(args.outfile))
