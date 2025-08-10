---
sidebar_position: 6
---

# Partial Application

Partial application in NumFu lets you call a function with *some* of its arguments now, producing a new function that remembers those arguments and waits for the rest.
This works for both user-defined lambdas and built-in functions, and becomes even more powerful with the **underscore (`_`) placeholder** syntax.

-----

## Currying and Partial Application

### Automatic Currying

One of NumFu's most powerful features is automatic currying:
when you provide fewer arguments than a function expects, you get back a new function.

```numfu
let add = {x, y -> x + y} in
let add5 = add(5) in   // Partial application
  add5(3)              // 8
```

Partially applied functions can also be inspected:

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

Providing more arguments than parameters is an error:

```numfu
let add = {x, y -> x + y} in
  add(1, 2, 3)
// TypeError: Cannot apply 1 more arguments to non-callable result
```

-----

## The `_` Placeholder

While currying applies arguments from left to right, the `_` placeholder lets you **skip** arguments in any position and fill them in later.

```numfu
max(_)([1, 2, 3])     // 3
max(_, 2, _)(1, 3)    // 3
max(1, _, _)(2)(3)    // 3
```

- Works in any position (start, middle, end)
- Works for both lambdas and built-in functions
- Multiple `_` placeholders allowed
- You can fill multiple placeholders in one later call

#### Examples with custom functions
```numfu
{a, b, c -> a + b + c}(_, 5, _)
// {a, c -> a + 5 + c}

{a, b, c -> a + b + c}(5, _)
// {b, c -> 5 + b + c}
```

#### Examples with built-ins
```numfu
max(_, _, _)(2, 3)    // partially applied function
max(2, _)(3, 4)       // 4
```

Placeholders remember fixed arguments and validate the rest when filled later.

-----
## Operators as Functions

In NumFu, operators like `+`, `-`, `>`, `==`, and many others are internally **just regular functions**.
This means you can use them anywhere you can use a function — including partial application with `_`.

This is especially useful for writing piping chains and simple helper functions without having to define lambdas explicitly.

```numfu
_ + 1
// is equivalent to:
{x -> x + 1}

10 > _
// is equivalent to:
{x -> 10 > x}
```

### Examples in Piping

```numfu
[1, 2, 3] |> map(_, _ * 2);
// [2, 4, 6]

[5, 12, 3] |> filter(_, _ > 4) |> map(_, _ * 2)
// [10, 24]
```

______
## Rest Parameters and `_`

Rest parameters (`...name`) collect all remaining arguments into a list.
They combine seamlessly with placeholders:

```numfu
{x, ...args -> args}(_, 1, 2)
// {x -> [1,2,2]}

{x, ...args -> args}(10, _, _, _)
// {...args -> args}
```

This also works for built-in functions that accept any number of arguments:

```numfu
max(2, _)(3, 4)       // 4
max(_, _, _)(2, 3)    // partially applied function
```

-----

## Restrictions

You **cannot** use `_` together with the spread (`...`) operator when calling a function:

```numfu
join(["a", "b"], ..._)
// TypeError: Cannot combine spread operator with argument placeholder
```

The spread operator requires fully evaluated values, not placeholders.

-----

## More Examples

```numfu
// Chain of partials
{a, b -> a * b}(2)
// {b -> 2 * b}

// Placeholder in middle, fill rest later
{a, b, c -> a + b * c}(_, 3)(4)
// {a -> a + 3 * 4}

{a, b, c -> a+b+c}(_, 5, _)
// {a,c -> a+5+c}

// With join
join(["x", "y"], _)("-")
// "x-y"
```

#### Rest parameters

```numfu
// Rest parameter with placeholders
{x, ...args -> args}(_, 1, 2)(5)
// [1, 2]

{x, ...args -> min(args) + x}(10, _, _, _)(1,2,3)
// 11

// Builtin function with multiple args in later call
max(5, _)(2, 8, 1)  // 8
```

#### Combining with piping

```numfu
5 |> max(_, 10)     // 10

// Creating a reusable partial function
let divideIt = {x, y -> x / y}(_, 2) in
10 |> divideIt      // 5

[5, 12, 3] |> filter(_, _ > 4) |> map(_, _ * 2)
// [10, 24]
```
