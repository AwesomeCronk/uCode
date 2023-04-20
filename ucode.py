import argparse, json5

_version = '2.1.0'


verbosityLevels = [
    'error',
    'info',
    'state',
    'step',
    'condition',
    'encode',
    'verify',
    'evaluate',
    'macro'
]

options = {
    'StateAddr': 'Binary',
    'StepAddr': 'Binary'
}

validOptions = {
    'StateAddr': ('Binary', 'PriorityEncode'),
    'StepAddr': ('Binary', 'PriorityEncode')
}

verbosityLevel = 1

def vPrint(verbosity, *args, **kwargs):
    if verbosityLevel >= verbosityLevels.index(verbosity):
        print(*args, **kwargs)


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
        type=str,
        default='1'
    )

    return parser.parse_args()


def verifyCondition(source, names):
    specialChars = '!&^|()'

    # No special characters in names
    for name in names:
        for char in specialChars:
            if char in name:
                vPrint('error', 'Invalid name: "{}"'.format(name))
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
        vPrint('error', 'Cannot put two names next to each other')
        return False
    
    # No non-special characters except for names
    for piece in pieces:
        for char in piece:
            if not char in specialChars:
                vPrint('error', 'Character "{}" not part of a name is invalid'.format(char))
                return False

    # No mismatching parentheses
    depth = 0
    for c, char in enumerate(source):
        if char == '(': depth += 1
        if char == ')': depth -= 1
        if depth < 0:
            vPrint('error', '")" at {} has no matching "("'.format(c))
            return False
    if depth != 0:
        vPrint('error', '"(" has no matching ")"')
        return False

    return True

def evaluateCondition(source, recursiveness=0, verbose=0):

    # a&b = a AND b
    # a^b = a XOR b
    # a|b = a OR b
    # !a = NOT a
    
    if source in ('0', '1'): return source
    vPrint('evaluate', '| ' * recursiveness + ',-Source: {}'.format(source))

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
        vPrint('evaluate', '| ' * recursiveness + '|-Parentheses {} thru {}'.format(beg, end))

        source = source[:beg] + evaluateCondition(source[beg+1:end], recursiveness+1) + source[end+1:]

    if '|' in source:
        chunks = [evaluateCondition(chunk, recursiveness+1) for chunk in source.split('|')]
        # OR the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            vPrint('evaluate', '| ' * recursiveness + '`-{} OR {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) | int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif '^' in source:
        chunks = [evaluateCondition(chunk, recursiveness+1) for chunk in source.split('^')]
        # XOR the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            vPrint('evaluate', '| ' * recursiveness + '`-{} XOR {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) ^ int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif '&' in source:
        chunks = [evaluateCondition(chunk, recursiveness+1) for chunk in source.split('&')]
        # AND the first two together and delete the second until there's only one left
        while len(chunks) > 1:
            vPrint('evaluate', '| ' * recursiveness + '`-{} AND {}'.format(*chunks[0:2]))
            chunks[0] = str(int(chunks[0]) & int(chunks[1]))
            del chunks[1]
        return chunks[0]
    
    elif source[0] == '!':
        chunk = evaluateCondition(source[1:], recursiveness+1)
        vPrint('evaluate', '| ' * recursiveness + '`-NOT {}'.format(chunk))
        if chunk == '0': return '1'
        else: return '0'
    
    else: return source


def macro_SetState(stateName, verbose):
    # Easier way of changing state
    # Requires that State_Set and State_0..State_N be available
    # Treats State_0 as LSB in address
    # All lists of bits have MSB at index 0

    result = [0] * numControlLines
    mask = [int(controlLine[0:6] == 'State_') for controlLine in controlLines]

    stateNum = stateOrder.index(stateName)
    bits = [int(bit) for bit in bin(stateNum)[2:].zfill(len(bin(numStates)[2:]) - 1)]   # State number as list of bits

    stateLines = ['State_Set']
    for i in range(len(bits)):
        if bits[i] == 1:
            stateLines.append('State_' + str(len(bits) - i - 1))

    vPrint('macro', '      State lines: {}'.format(stateLines))

    for line in stateLines:
        result[controlLines.index(line)] = 1

    return result, mask

macros = {
    'SetState': macro_SetState
}

def encodeStep(step, verbose):
    bits = [0] * numControlLines

    for entry in step:
        if entry[0] == '/':
            macroName = entry.split(':')[0][1:]
            macroArgs = entry.split(':')[1:]
            vPrint('encode', '      Macro: {}, Args: {}'.format(macroName, macroArgs))
            result, mask = macros[macroName](*macroArgs, verbose)
            vPrint('encode', '      Result: {}'.format(''.join([str(i) for i in result])))
            vPrint('encode', '      Mask:   {}'.format(''.join([str(i) for i in mask])))
    
            for i in range(numControlLines):
                if mask[i]: bits[i] = result[i]

        else:
            bits[controlLines.index(entry)] = 1
        

    # Convert bit list to bytes and return
    intValue = 0
    for bit in bits: intValue <<= 1; intValue |= bit
    return int.to_bytes(intValue, numControlLines // 8, 'big')


if __name__ == '__main__':
    args = getArgs()
    try:
        verbosityLevel = int(args.verbose)
    except ValueError:
        if args.verbose in verbosityLevels:
            verbosityLevel = verbosityLevels.index(args.verbose)
        else:
            vPrint('error', 'Invalid verbosity "{}"'.format(args.verbose)); exit(1)
    vPrint('info', 'uCode {}'.format(_version))


    ### Load JSON5 source ###

    with open(args.infile, 'r') as jsonFile: json = json5.load(jsonFile)

    try: numControlLines      = json['NumControlLines']
    except KeyError: vPrint('error', 'NumControlLines not defined'); exit(1)

    try: numConditionLines    = json['NumConditionLines']
    except KeyError: vPrint('error', 'NumConditionLines not defined'); exit(1)

    try: numStates            = json['NumStates']
    except KeyError: vPrint('error', 'NumStates not defined'); exit(1)

    try: numSteps             = json['NumSteps']
    except KeyError: vPrint('error', 'NumSteps not defined'); exit(1)

    try: controlLines         = json['ControlLines']
    except KeyError: vPrint('error', 'ControlLines not defined'); exit(1)

    try: conditionLines       = json['ConditionLines']
    except KeyError: vPrint('error', 'ConditionLines not defined'); exit(1)

    try: states               = json['States']
    except KeyError: vPrint('error', 'States not defined'); exit(1)

    try: stateOrder           = json['StateOrder']
    except KeyError: vPrint('error', 'StateOrder not defined'); exit(1)


    if 'Options' in json.keys():
        chosenOptions = json['Options']
        for key in chosenOptions.keys():

            try:
                value = chosenOptions[key]
                
                if not value in validOptions[key]:
                    vPrint('error', 'Invalid option value {} for {}'.format(value, key))
                    exit(1)
                
                options[key] = value

            except KeyError:
                vPrint('error', 'Invalid option key {}'.format(key))
                exit(1)


    ### Verify line, condition, state, and step counts ###

    if len(controlLines) != numControlLines:
        vPrint('error', 'Control line count {} invalid, expected {}'.format(len(controlLines), numControlLines))
        exit(1)
    if numControlLines % 8 != 0:
        vPrint('error', 'Control line count {} invalid, must be a multiple of 8'.format(numControlLines))
        exit(1)
    if len(conditionLines) != numConditionLines:
        vPrint('error', 'Condition line count {} invalid, expected {}'.format(len(conditionLines), numConditionLines))
        exit(1)
    
    # If option `StateAddr` is set to `PriorityEncode` then a fallback state needs to be defined
    if options['StateAddr'] == 'Binary': actualNumStates = numStates
    elif options['StateAddr'] == 'PriorityEncode': actualNumStates = numStates + 1

    # If option `StepAddr` is set to `PriorityEncode` then a fallback step can be defined (will use defaultStep if not)
    if options['StepAddr'] == 'Binary': actualNumSteps = numSteps
    elif options['StepAddr'] == 'PriorityEncode': actualNumSteps = numSteps + 1

    if len(stateOrder) != actualNumStates: 
        vPrint('error', 'State order count {} invalid, expected {}'.format(len(stateOrder), actualNumStates))
        exit(1)

    for stateName in stateOrder:
        if len(states[stateName]) > actualNumSteps:
            vPrint('error', 'State {} step count {} invalid, exceeds {}'.format(stateName, len(states[stateName]), actualNumSteps))
            exit(1)


    ### Encode the steps of each state ###

    # Iterate states
    stateBinaries = []
    for stateName in stateOrder:
        state = states[stateName]
        vPrint('state', 'State {}:'.format(stateName))

        # Allows states to leave off any steps which need not be specified
        # If a state needs less steps than specified, it can define only what it needs and the rest will be filled in

        while len(states[stateName]) < actualNumSteps:
            try:
                states[stateName].append(json['DefaultStep'])
            except KeyError:
                vPrint('error', 'Not all steps defined in state {} but DefaultStep is not defined'.format(stateName))
                exit(1)

        # Iterate steps
        stepBinaries = []
        for s, step in enumerate(states[stateName]):
            vPrint('step', '  Step {}: '.format(s), end='')
            stepBinary = b''

            # Steps can be a list of control lines and be constant
            if isinstance(step, list):
                if len(step) == 0:
                    vPrint('step', 'blank')
                    stepBinary = stepBinary + b'\x00' * ((numControlLines // 8) * (2 ** numConditionLines))

                else:
                    vPrint('step', 'constant')
                    for k in range(2 ** numConditionLines):
                        stepBinary = stepBinary + encodeStep(step, args.verbose)

            # Or can be a dict of conditions and outputs and be conditional
            elif isinstance(step, dict):
                vPrint('step', 'conditional')
                validCases = [[None] * len(step) for _ in range(2 ** numConditionLines)]    # List of lists; indexed by case number, sublists indexed by condition number

                for i0, condition in enumerate(step.keys()):
                    vPrint('condition', '    Condition: "{}"'.format(condition))
                    if condition != '':
                        if not verifyCondition(condition, conditionLines): exit(1)  # `verifyCondition` will print the reason

                        for i1 in range(2 ** numConditionLines):
                            evaluatable = condition
                            bits = list(bin(i1)[2:].zfill(len(conditionLines)))
                            # print('Bits:', bits)
                            for i2, conditionLine in enumerate(conditionLines):
                                evaluatable = evaluatable.replace(conditionLine, bits[i2])
                            
                            validCases[i1][i0] = evaluateCondition(evaluatable, args.verbose) == '1'
                
                # print('    Valid cases:')
                # for i in validCases: print('    {}'.format(i))

                lines = list(step.values())
                vPrint('condition', '    Lines: {}'.format(lines))

                for i0, case in enumerate(validCases):
                    # vPrint('condition', '    Case: {}, Matches: {}'.format(case, case.count(True)))
                    
                    if case.count(True) == 1:
                        vPrint('condition', '    Chose: {}'.format(lines[case.index(True)]))
                        stepBinary = stepBinary + encodeStep(lines[case.index(True)], args.verbose)

                    elif case.count(True) == 0:
                        vPrint('condition', '    Chose: {}'.format(lines[case.index(None)]))
                        stepBinary = stepBinary + encodeStep(lines[case.index(None)], args.verbose)

                    else:
                        matchingConditions = []
                        for i1, match in enumerate(case):
                            if match:
                                matchingConditions.append(step.keys()[i1])

                        vPrint('error', 'Case {} matches multiple conditions: "{}"'.format(bin(i0)[2:], '", "'.join(matchingConditions)))
            
            else:
                vPrint('error', 'Step {} must be of type list or dict'.format(s))
                exit(1)

            stepBinaries.append(stepBinary)
        

        # Compile step binaries to form a state binary
        vPrint('encode', 'Addressing steps in {} mode'.format(options['StepAddr']))
        
        if options['StepAddr'] == 'Binary':
            stateBinary = b''.join(stepBinaries)

        elif options['StepAddr'] == 'PriorityEncode':
            # See addressing table below
            stateBinary = stepBinaries[-1]  # Puts the fallback at address 0
            for s, stepBinary in enumerate(stepBinaries[0:-1]):
                stateBinary = stateBinary + (stepBinary * (2 ** s))

        stateBinaries.append(stateBinary)


    # Compile state binaries to form the full binary
    vPrint('encode', 'Addressing states in {} mode'.format(options['StateAddr']))
    
    if options['StateAddr'] == 'Binary':
        fullBinary = b''.join(stateBinaries)

    elif options['StateAddr'] == 'PriorityEncode':
        # See addressing table below
        fullBinary = stateBinaries[-1]  # Puts the fallback at address 0
        for s, stateBinary in enumerate(stateBinaries[0:-1]):
            fullBinary = fullBinary + (stateBinary * (2 ** s))


    # Addressing table for ProrityEncode modes
    # 0000 0: Blank
    # 0001 1: Step0
    # 0010 2: Step1
    # 0011 3: Step1
    # 0100 4: Step2
    # 0101 5: Step2
    # 0110 6: Step2
    # 0111 7: Step2
    # 1000 8: Step3
    # 1001 9: Step3
    # 1010 A: Step3
    # 1011 B: Step3
    # 1100 C: Step3
    # 1101 D: Step3
    # 1110 E: Step3
    # 1111 F: Step3
    
    with open(args.outfile, 'wb') as file: file.write(fullBinary)
    vPrint('info', 'Wrote binary to {}'.format(args.outfile))
