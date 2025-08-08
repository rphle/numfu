---
sidebar_position: 5
---

# Functions and Lambdas

As a functional programming language, NumFu treats functions as first-class values that can be created, passed around, and composed to build complex programs from simple parts.

-----
## Lambda Basics

### Creating Simple Functions

In NumFu, functions are created using lambda expressions with the syntax `{parameters -> body}`:

```numfu
{x -> x + 1}                    // Function that adds 1
{x -> x * x}                    // Function that squares a number
{name -> "Hello, " + name}      // Function that creates a greeting
```

### Calling Functions

Call functions using parentheses:

```numfu
let square = {x -> x * x} in square(5)     // 25
let greet = {name -> "Hello, " + name} in greet("NumFu")  // "Hello, NumFu"
```

### Inline Function Calls

You can call lambda expressions directly:

```numfu
{x -> x + 1}(10)               // 11
{x, y -> x * y}(3, 4)          // 12
```

-----
## Multiple Parameters

### Multiple Arguments

Functions can accept multiple parameters separated by commas:

```numfu
{x, y -> x + y}                // Addition function
{a, b, c -> a * b + c}         // Linear function
```
```numfu
let say = {name, age -> format("{} is {} years old", name, age)} in
  say("John", 42)
// John is 42 years old
```

-----
## Currying and Partial Application

### Automatic Currying

One of NumFu's most powerful features is automatic currying. When you provide fewer arguments than a function expects, you get back a new function:

```numfu
let add = {x, y -> x + y} in
let add5 = add(5) in             // Partial application
  add5(3)                        // 8
```

Partially applied functions can also be printed:
```numfu
{x, y -> x + y}(5)
// {y -> 5 + y}
```

### Progressive Application

You can apply arguments one at a time:

```numfu
let multiply = {x, y, z -> x * y * z} in
let double = multiply(2) in      // {y, z -> 2 * y * z}
let doubleBy3 = double(3) in     // {z -> 2 * 3 * z}
  doubleBy3(4)                   // 24
```

### Too Many Arguments

Providing too many arguments is an error:

```numfu
let add = {x, y -> x + y} in
  add(1, 2, 3)
// TypeError: Cannot apply 1 more arguments to non-callable result
```

-----
## Named Functions

### Named Lambda Syntax

You can give functions names using the syntax `{name: parameters -> body}`:

```numfu
{divide: a, b -> a / b}
```

### Top-Level Named Functions

Named functions at the top level act like constants:

```numfu
{printImportant: text -> println("Important: " + text)}

// Now printImportant is available everywhere in the file
printImportant("Cookies are delicious")
// Important: Cookies are delicious
```

### Recursive Functions

Named functions can call themselves recursively:

```numfu
{fibonacci: n ->
  if n <= 1 then n
  else fibonacci(n - 1) + fibonacci(n - 2)
}

fibonacci(10)    // 55
```

-----
## Rest Parameters

### Collecting Extra Arguments

Use `...paramName` to collect remaining arguments into a list:

```numfu
{first, ...rest -> [first, rest]}(1, 2, 3, 4, 5)
// [1, [2, 3, 4, 5]]

{...args -> length(args)}(1, 2, 3)    // 3
```

Each function can only have a single rest parameter which must come at the end.


### Example

```numfu
{sum: ...numbers ->
  let helper = {nums, acc ->
    if length(nums) == 0 then acc
    else helper(slice(nums, 1, -1), acc + nums[0])
  } in helper(numbers, 0)
}

sum(1, 2, 3, 4, 5)    // 15
```

-----
## Higher-Order Functions

### Functions That Accept Functions

Functions can take other functions as parameters:

```numfu
let twice = {f, x -> f(f(x))} in
let add1 = {x -> x + 1} in
  twice(add1, 5)                // 7 (add1(add1(5)))
```

### Functions That Return Functions

Functions can return other functions:

```numfu
let makeAdder = {n -> {x -> x + n}} in
let add10 = makeAdder(10) in
  add10(5)                      // 15
```

### Function Factories

Create specialized functions using function factories:

```numfu
let makePowerFunction = {exponent ->
  {base -> base ^ exponent}
} in
let square = makePowerFunction(2) in
let cube = makePowerFunction(3) in
  [square(4), cube(3)]    // [16, 27]
```

-----
## Closures

### Capturing Environment

Functions capture variables from their surrounding environment:

```numfu
let multiplier = 10 in
let scale = {x -> x * multiplier} in
  scale(5)     50
```

### Closures Preserve Values

Even when the original scope ends, the captured values remain:

```numfu
let makeCounter = {start ->
  let current = start in
    {increment -> current + increment}
} in
let counter = makeCounter(100) in
  counter(5)    // 105
```

-----
## Examples

### Configurable Greeting
```numfu
// Create a configurable greeting function
let makeGreeting = {greeting, punctuation, name ->
  greeting + ", " + name + punctuation
} in
let casual = makeGreeting("Hi") in
let casualExcited = casual("!") in
  casualExcited("Alice")        // "Hi, Alice!"
```

### Conditional Function Selection

Choose functions based on conditions:

```numfu
let operation = "square" in
let processor = if operation == "square" then {x -> x * x}
                else if operation == "double" then {x -> x * 2}
                else {x -> x} in
  processor(6)    // 36
```

### Mathematical Functions

```numfu
// Distance between two points
{distance: x1, y1, x2, y2 ->
  let dx = x2 - x1, dy = y2 - y1 in
    sqrt(dx^2 + dy^2)
}

distance(0, 0, 3, 4)    // 5
```

### Function Composition Function

```numfu
// Compose multiple functions
let compose = {f, g -> {x -> f(g(x))}} in

let add1 = {x -> x + 1} in
let double = {x -> x * 2} in

compose(double, add1)(5)    // 12 (double(add1(5)))
```

### Higher-Order Functions
```numfu
// Create a function that applies another function twice
let applyTwice = {f, x -> f(f(x))} in
let increment = {x -> x + 1} in
  applyTwice(increment, 10)    // 12
```

```numfu
// Create a function that creates multiplier functions
let makeMultiplier = {factor -> {x -> x * factor}} in
let triple = makeMultiplier(3) in
  triple(7)    // 21
```

### Recursive Functions
```numfu
// Factorial function
{factorial: n ->
  if n <= 1 then 1
  else n * factorial(n - 1)
}
factorial(5)    // 120
```

```numfu
// Square root using Newton's method
let sqrt = {x ->
  let improve = {guess -> (guess + x / guess) / 2} in
    let iterate = {guess, n ->
      if n <= 0 then guess
      else iterate(improve(guess), n - 1)
    } in iterate(x / 2, 10)
} in sqrt(25)    // 5
```
