# uCode
This is a microcode generation tool for homebrew CPU building. It was originally developed as a script within my [SiliconPython](https://github.com/AwesomeCronk/SiliconPython) project, but soon outpaced it in terms of completeness and usability, so I have published it here.

## Installation
Linux and Windows binaries will be available soon. In the meantime, you can download the python script and use it as-is.

## Usage
To generate microcode, you need to create a file, say `ucode.json5` and write your microcode description in it. uCode uses JSON5 to format these files. See [the example](/example.json5) for an example on how it works. I'm trying to figure out a tutorial, so if you need help, DM Discord user `AwesomeCronk#7410`

### Options

Description files can include an `Options` section containing key/value pairs. These options include:

1. `StateAddr`
   1. `Binary` (default): Normal binary addressing
   2. `PriorityEncode`: Priority encoded with the last state being the inactive state  
2. `StepAddr`
   1. `Binary` (default): Normal binary addressing
   2. `PriorityEncode`: Priority encoded with the last state being the inactive state
