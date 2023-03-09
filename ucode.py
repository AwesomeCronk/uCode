import argparse, json5

_version = '1.0.0'

def getArgs():
    parser = argparse.ArgumentParser('uCode', description='Generates microcode ROM binaries. See https://github.com/AwesomeCronk/uCode for more information.')
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

if __name__ == '__main__':
    print('uCode {}'.format(_version))
    args = getArgs()

    with open(args.infile, 'r') as jsonFile: json = json5.load(jsonFile)

    lines = json['lines']
    states = json['states']
    stateOrder = json['stateOrder']
    numLines = json['numLines']             # Control lines
    numConditions = json['numConditions']   # Condition inputs
    numStates = json['numStates']
    numSteps = json['numSteps']

    if len(lines) != numLines: print('Line count {} is incorrect'.format(len(lines))); exit()
    if len(stateOrder) != numStates: print('State order count {} is incorrect'.format(len(stateOrder))); exit()
    for s, state in enumerate(states):  # `s` is state name, `state` is state contents
        if len(json[state]) > numSteps and s in stateOrder:
            print('Too many steps ({}) for state {}'.format(len(json[state]), s)); exit()

    def encodeStep(step):
        bits = [0] * len(lines)

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
            for line in stateLines: bits[len(lines) - lines.index(line) - 1] = 1

        # Normal step encoding
        else:
            for line in step: bits[len(lines) - lines.index(line) - 1] = 1

        # Convert bits to bytes and return
        intValue = 0
        for bit in bits: intValue *= 2; intValue += bit
        return int.to_bytes(intValue, len(lines) // 8, 'big')

    def evaluatePrecedence(source, recursiveness=0):

        # a&b = a AND b
        # a^b = a XOR b
        # a|b = a OR b
        # !a = NOT a

        if source in ('0', '1'): return source
        # print('  ' * recursiveness + 'Source: {}'.format(source))

        while '(' in source or ')' in source:
            depth = 1
            i = 0
            char = source[i]

            # Seek to first `(`
            while char != '(':
                if char == ')': raise SyntaxError('unmatched ")" at {}'.format(i))    # Catches a `)` before any `(`
                i += 1
                char = source[i]

            beg = i
            
            while depth != 0:
                if depth < 0: raise SyntaxError('unmatched ")" at {}'.format(i))
                i += 1
                if i >= len(source): raise SyntaxError('Unmatched "(" at {}'.format(beg))
                char = source[i]
                if char == '(': depth += 1
                elif char == ')': depth -= 1

            end = i
            # print('  ' * recursiveness + 'Parentheses {} thru {}'.format(beg, end))
            source = source[:beg] + evaluatePrecedence(source[beg+1:end], recursiveness+1) + source[end+1:]

        if '|' in source:
            chunks = [evaluatePrecedence(chunk) for chunk in source.split('|')]
            # OR the first two together and delete the second until there's only one left
            while len(chunks) > 1:
                # print('  ' * recursiveness + '{} OR {}'.format(*chunks[0:2]))
                chunks[0] = str(int(chunks[0]) | int(chunks[1]))
                del chunks[1]
            return chunks[0]
        
        elif '^' in source:
            chunks = [evaluatePrecedence(chunk) for chunk in source.split('^')]
            # XOR the first two together and delete the second until there's only one left
            while len(chunks) > 1:
                # print('  ' * recursiveness + '{} XOR {}'.format(*chunks[0:2]))
                chunks[0] = str(int(chunks[0]) ^ int(chunks[1]))
                del chunks[1]
            return chunks[0]
        
        elif '&' in source:
            chunks = [evaluatePrecedence(chunk) for chunk in source.split('&')]
            # AND the first two together and delete the second until there's only one left
            while len(chunks) > 1:
                # print('  ' * recursiveness + '{} AND {}'.format(*chunks[0:2]))
                chunks[0] = str(int(chunks[0]) & int(chunks[1]))
                del chunks[1]
            return chunks[0]
        
        elif source[0] == '!':
            chunk = evaluatePrecedence(source[1:])
            # print('  ' * recursiveness + 'NOT {}'.format(chunk))
            if chunk == '0': return '1'
            else: return '0'
        
        else: return source
    binary = b''

    for s in stateOrder:
        state = states[s]
        if args.verbose >= 1: print('State {}: {}'.format(s, state))

        # Allows states to leave off any steps which need not be specified
        # If a state needs less steps than specified, it can define only what it needs and the rest will be filled in
        while len(state) < numSteps: state.append(json['defaultStep'])

        for step in state:
            if isinstance(step, list):
                if args.verbose >= 2: print('Constant step')
                # Need to cover the whole address range that the condition lines might select (2 ** numConditions)
                binary += encodeStep(step) * (2 ** numConditions)

            elif isinstance(step, dict):
                if args.verbose >= 2: print('Conditional step')
                for i in range(2 ** numConditions):
                    matches = []
                    for condition in step.keys():
                        



    for i, state in enumerate(states):
        if args.verbose >= 1: print('State {}: {}'.format(i, state))

        # Allows states to leave off any steps which need not be specified
        # If a state needs less steps than specified, it can define only what it needs and the rest will be filled in
        while len(json[state]) < numSteps: json[state].append(json['defaultStep'])

        for j, step in enumerate(json[state]):
            if args.verbose >= 2: print('  Step {}: '.format(j), end='')

            # Steps can be a list of lines and be constant
            # or can be a list of lists of lines and be conditional
            if len(step) == 0:
                if args.verbose >= 2: print('blank')
                binary = binary + b'\x00' * ((len(lines) // 8) * numConditions)
            elif isinstance(step[0], list):
                if args.verbose >= 2: print('conditional')
                assert len(step) == numConditions
                for k, conditional in enumerate(step):
                    binary = binary + encodeStep(conditional)
            else:
                if args.verbose >= 2: print('constant')
                for k in range(numConditions):
                    binary = binary + encodeStep(step)

    with open(args.outfile, 'wb') as file: file.write(binary)
    print('Wrote binary to {}'.format(args.outfile))
