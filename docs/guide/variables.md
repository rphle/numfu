# Variables and Let Expressions

In NumFu, variables can be created in two ways:
1. Using `let` bindings with `in`, which create local scopes for values
2. Using top-level `let` statements, which define program-wide variables

This provides both functional scoping and practical module-level state management.

-----
## Let Bindings

Let bindings create local scopes and return values. The basic syntax is `let name = value in expression`:

```numfu
let x = 42 in x              // 42
let name = "NumFu" in name   // "NumFu"
let flag = true in flag      // true
```

The variable `x` is only available within the `in` part of the expression.

### Using Variables in Calculations

Variables become powerful when used in calculations:

```numfu
let radius = 5 in pi * radius^2        // Circle area: ~78.54

let price = 100 in
let tax = 0.08 in
  price * (1 + tax)                     // Price with tax: 108
```

### Let Expressions Return Values

Remember that `let` expressions return the value of the `in` part:

```numfu
let result = let x = 10
    in x * 2
  in result + 5  // 25
```

-----
## Multiple Variable Bindings

### Comma-Separated Bindings

You can define multiple variables in a single `let` expression. All variables defined in the same `let` are available throughout the `in` body:

```numfu
let x = 3, y = 4 in x^2 + y^2             // 25

let first = "Hello", second = "World" in
  first + " " + second                    // "Hello World"

let a = 1, b = 2, c = 3 in a + b + c      // 6
```


### Mutual Reference

Variables in the same `let` *cannot* reference each other:

```numfu
let x = y + 1, y = 5 in x
// NameError: 'y' is not defined in the current scope
```

-----
## Variable Scoping

### Lexical Scoping

NumFu uses lexical (static) scoping - variables are accessible where they're defined:

```numfu
let outer = 10 in
  let inner = 20 in
    outer + inner    // 30 - both variables accessible
```

### Nested Scoping

Inner scopes have access to outer scopes:

```numfu
let a = 1 in
  let b = 2 in
    let c = 3 in
      a + b + c    // 6
```

### Scope Boundaries

Variables are only accessible within their scope:

```numfu
let x = 10 in x + 5    // 15
x    // NameError: 'x' is not defined in the current scope
```

-----
## Variable Shadowing

### Inner Variables Shadow Outer Ones

When you define a variable with the same name in an inner scope, it "shadows" the outer one:

```numfu
let x = 10 in
  let x = 20 in
    x    // 20 (inner x)
```

### Original Values Preserved

The outer variable is unchanged by shadowing:

```numfu
let x = 10 in
  let result = let x = 20 in x in
    [x, result]    // [10, 20]
```

### Practical Shadowing

Shadowing is useful for transforming values step by step:

```numfu
import trim, toLowerCase, replace from "std"

let data = "  Hello World  " in
let data = trim(data) in                // Remove whitespace
let data = toLowerCase(data) in         // Convert to lowercase
let data = replace(data, " ", "_") in   // Replace spaces
  data                                  // "hello_world"
```

-----
## Let Statements

Let statements define variables that are available throughout your program:

```numfu
import * from "io"

let PI = 3.14159
let greeting = "Welcome to NumFu!"

// These are available in all expressions below
println(greeting)
print("pi^2 = ")
PI^2
```

Let statements must be at the module (file) level and can only assign one variable at a time:

```numfu
let x = 5 in
  let INVALID = 10
// SyntaxError: Missing 'in' — bare 'let' allowed only at top level

let a = 1, b = 2
// SyntaxError: Cannot assign multiple identifiers here
```

## Deleting Variables

To remove a variable which was previously declared using a let statement, use the `del` statement:

```numfu
let temp = "temporary"
// ... use temp ...
del temp  // Variable is no longer available
```

Like let statements, `del` statements can only be used at the module (file) level.

## Variable Naming

The keywords and special symbols listed below cannot be used as variable names or function parameters. The parser will throw an error if you try to use them.

`let`, `in`, `if`, `then`, `else`, `del`,`import`, `export`, `from`, `true`, `false`, `$`, `_`

-----
## Examples

### Basic Variable Usage

```numfu
import pi from "math"
// Calculate the volume of a cylinder
let radius = 3, height = 10 in
let baseArea = pi * radius^2 in
  baseArea * height    // ~282.74
```

```numfu
// Convert temperature scales
let celsius = 25 in
let fahrenheit = celsius * 9/5 + 32 in
let kelvin = celsius + 273.15 in
  [celsius, fahrenheit, kelvin]    // [25, 77, 298.15]
```

### Scoping

```numfu
let outer = "outer" in
  let inner = "inner" in
    let result = outer + " and " + inner in
      result    // "outer and inner"
```

```numfu
let x = 1 in
  let x = x + 1 in
    let x = x * 2 in
      x    // 4
```


### Multiple Bindings

```numfu
import sqrt from "math"

let point = [3, 4] in
let x = point[0], y = point[1] in
  sqrt(x^2 + y^2)
// Distance from origin: 5
```

```numfu
// Calculate a student's final score
let homeworkAvg = 85, testAvg = 92, finalExam = 88 in
let homeworkWeight = 0.3, testWeight = 0.4, finalWeight = 0.3 in
  homeworkAvg * homeworkWeight +
  testAvg * testWeight +
  finalExam * finalWeight
// 88.7
```

### Intermediate Calculations

Quadratic formula: x = (-b ± √(b²-4ac)) / 2a

```numfu
import sqrt from "math"

let a = 1, b = -5, c = 6 in
let discriminant = b^2 - 4*a*c in
let sqrt_discriminant = sqrt(discriminant) in
let x1 = (-b + sqrt_discriminant) / (2*a) in
let x2 = (-b - sqrt_discriminant) / (2*a) in
  [x1, x2]    // [3, 2]
```
