# uCode
This is a microcode generation tool for homebrew CPU building. It was originally developed as a script within my [SiliconPython](https://github.com/AwesomeCronk/SiliconPython) project, but soon outpaced it in terms of completeness and usability, so I have published it here.

## Installation
Nothing yet, but the Python script is provided if you want to use it as-is.

## Usage
To generate microcode, you need to create a file, say `ucode.json5` and write your microcode description in it. uCode uses JSON5 to format these files. This is pretty much the bare minimum:

```js
{
    numLines: 8,
    numStates: 1,
    numSteps: 8,
    numConditions: 2,

    lines: [
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        ''
    ],

    defaultStep: [],

    state_main: [

    ],

    states: [
        'state_main'
    ]
}
```

`numLines` tells uCode how many control lines there *should* be. If the length of `lines` does not batch this, uCode will exit early. Same story with `numStates` and `states`. It is highly recommended that `numLines` be a multiple of 8 to avoid any messes with sub-byte ordering. It is also highly recommended that `numStates` be a power of 2 to ensure that the generated binary completely fills the address space of the ROM.

All of the states you desire may be defined in a file, however only the states listed in `states` will be put in the binary. If there are unused states, the simplest way I know of to fill them is to use a blank state and just pad out `states` with it:

```js
    numStates: 4,
...
    state_blank: [],
...
    states: [
        'state_init',
        'state_run',
        'state_blank',
        'state_blank'
    ]
```

States are lists containing lists of control lines to enable. Each of these lists is referred to as a step. If you don't need to use all the steps in a specific state, you can leave them undefined and uCode will fill them in with `defaultStep`. Steps can be constant or conditional. A constant step is defined as a list of control lines; a conditional step is defined as a list of lists of control lines:

```js
    // A constant step
    ['MemData_Out', 'RegA_In'],
    
    // A conditional step
    [
        ['RegSum_Out', 'MemData_In'],
        ['RegFlags_Out', 'MemData_In']
    ]
```

`numConditions` tells uCode how many conditions the condition lines can describe. 2 condition lines is `2^2` or 4 conditions, 3 condition lines is `2^3` or 8 conditions, etc. Conditional steps are indexed with the integer value of the condition to which they correlate. Conditional steps must define the same number of conditions that `numConditions` defines.

To switch states when multiple states are defined, you can build your own logic or use uCode's builtin switching syntax. This requires that the control lines `State_Set`, `State_0`, `State_1`, and so on (sufficient to encode `numStates`) are defined. This can be used in either a constant or conditional state. State switching syntax puts `State_Set` and a state name, joined by `>>` as a single controll line in a step: `['State_Set>>state_name']`.
