# Imports and Exports

NumFu supports a robust module system that allows you to organize and reuse code across multiple files. This guide explains how to work with modules, import functionality from other files, and export values for use in other modules.

-----
## Basic Module Structure

A module in NumFu is simply a file with the `.nfu` extension that can contain any valid NumFu code. Modules can define constants, functions, and other values, and can choose which of these to make available to other modules.

```numfu
// math_utils.nfu
const PI = 3.14159
const square = x -> x * x
const cube = x -> x * x * x

export PI, square, cube
```

-----
## Exports

To make values available to other modules, use the `export` keyword followed by a comma-separated list of identifiers:

```numfu
const greeting = "Hello, World!"
export greeting

const VERSION = "1.0.0"
const add = {a, b -> a + b}
const sub = {a, b -> a - b}

export VERSION, add, sub
```
You can use multiple export statements in a single file.

### Export with Assignment

You can also directly export a value at the same time you define it:

```numfu
export my_export = 5 + 2
export double = x -> x * 2
```

-----
## Imports

### Named Imports
The most common way to import specific values from a module is using named imports:

```numfu
import PI, square from "math_utils"

square(PI)  // Uses both imported values
```

### Wildcard Imports
To import all exported values from a module, use the `*` syntax:

```numfu
import * from "math_utils"

// All exported values are now available
PI
square(3)
cube(2)
```

### Module-Prefixed Imports
When importing without specifying names, the module's exports are prefixed with the module name:

```numfu
import "math_utils"

math_utils.PI
math_utils.square(4)
```

### Import Organization
All imports *must* be placed at the top of your file, before any other code. This is a strict requirement enforced by the NumFu parser:

```numfu
// Correct:
import PI, E from "math_constants"
import square, cube from "math_functions"
import format from "string_utils"

const result = square(PI)  // Code after imports

// Incorrect - will raise a syntax error:
const x = 42
import format from "string_utils"  // SyntaxError: Imports allowed only at top level
```

-----
## Module Resolution

NumFu follows a specific order when resolving module imports:

1. **Local Files**: First checks for a `.nfu` file in the same directory
2. **Folders**: Looks for directories with an `index.nfu` file
3. **Standard Library**: Checks the built-in standard library

### File-based Modules
For a simple file-based module:

```numfu
// Imports from mymodule.nfu in the same directory
import value from "mymodule"
```

### Directory Modules
A directory can be treated as a module if it contains an `index.nfu` file. This is useful for organizing related functionality into a single namespace:

```numfu
// Directory structure:
// utils/
//   ├── index.nfu     // Exports everything
//   ├── math.nfu      // Math utilities
//   └── string.nfu    // String utilities

// In utils/index.nfu:
import * from "math"     // Re-export from math.nfu
import * from "string"   // Re-export from string.nfu

// In your main file:
import add, multiply from "utils"  // Imports from utils/index.nfu
```

Directory modules enable you to:
- Group related functionality
- Create hierarchical module structures
- Provide a single entry point for multiple sub-modules
- Control what gets exposed through the index file

### Relative Imports
Modules can import from relative paths:

```numfu
// From a file in parent directory
import value from "../shared"

// From a subdirectory
import util from "./utils/helpers"
```
