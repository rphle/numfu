# Booleans and Logic

NumFu's boolean system handles true/false values and logical operations with some unique features like chained comparisons and truthiness rules.

-----
## Boolean Literals

NumFu has two boolean values:

```numfu
true
false
```

These are the foundation of all logical operations and conditional logic in NumFu.

-----
## Comparison Operators

### Basic Comparisons

Compare values to get boolean results:

```numfu
5 == 5       // Equality: true
5 != 3       // Inequality: true
7 > 3        // Greater than: true
2 < 5        // Less than: true
5 >= 5       // Greater or equal: true
3 <= 7       // Less or equal: true
```

### Chained Comparisons

NumFu supports mathematical-style chained comparisons:

```numfu
1 < 2 < 3            // true (1 < 2 AND 2 < 3)
5 > 3 > 1            // true (5 > 3 AND 3 > 1)
1 < 2 > 3            // false (1 < 2 is true, but 2 > 3 is false)

// Equivalent to:
1 < 2 && 2 < 3       // true
5 > 3 && 3 > 1       // true
1 < 2 && 2 > 3       // false
```

-----
## Logical Operators

### AND Operator (`&&`)

Both conditions must be true:

```numfu
true && true         // true
true && false        // false
false && true        // false
false && false       // false
```

### OR Operator (`||`)

At least one condition must be true:

```numfu
true || true         // true
true || false        // true
false || true        // true
false || false       // false
```

### NOT Operator (`!`)

Inverts the boolean value:

```numfu
!true               // false
!false              // true
!!true              // true (double negation)
```

### XOR Function

Exclusive OR - exactly one must be true:

```numfu
xor(true, false)     // true
xor(false, true)     // true
xor(true, true)      // false
xor(false, false)    // false
```

-----
## Short-Circuit Evaluation

NumFu uses short-circuit evaluation for efficiency and safety. If the first operand is false, the second isn't evaluated:

```numfu
// AND
false && println("This won't print")  // false, no side effect
```
```numfu
// OR
true || println("This won't print, too")   // true, no side effect
```

-----
## Truthiness

NumFu values have "truthiness" when used in boolean contexts:

### Truthy Values
- `true`
- Non-zero numbers
- Non-empty strings
- Non-empty lists

### Falsy Values
- `false`
- `0` (zero)
- `""` (empty string)
- `[]` (empty list)

```numfu
!0             // true
!42            // false
!""            // true
!"hello"       // false
![]            // true
![1, 2]        // false
```


-----
## If-Then-Else Statements

Conditional logic in NumFu is handled using `if-then-else` statements. These statements allow you to evaluate different blocks of code based on whether a condition evaluates to `true` or `false`.

```numfu
if condition then
  // Code to evaluate if condition is true
else
  // Code to evaluate if condition is false
```

```numfu
let x = 10 in
if x > 5 then
  println("x is greater than 5")
else
  println("x is 5 or less")
```

### Nested If-Then-Else

You can nest `if-then-else` statements to handle more complex conditions:

```numfu
import println from "io"

let score = 85 in
if score >= 90 then
  println("Grade: A")
else if score >= 80 then
  println("Grade: B")
else if score >= 70 then
  println("Grade: C")
else if score >= 60 then
  println("Grade: D")
else
  println("Grade: F")
```

### If-Then-Else as an Expression

In NumFu, `if-then-else` can also be used as an expression that returns a value:

```numfu
let x = 10 in
let result = if x > 5 then "greater than 5" else "5 or less" in
println(result)
```


-----
## Examples

### Range Checking

```numfu
let age = 25 in
  age >= 18 && age < 65  // true (working age)

let score = 85 in
  score >= 0 && score <= 100  // true (valid score)
```

### Complex Conditions

```numfu
let temperature = 22 in
let humidity = 45 in
let isComfortable =
  temperature >= 20 && temperature <= 25 &&
  humidity >= 30 && humidity <= 60 in
  isComfortable  // true
```

### Guard Clauses

```numfu
import format from "std"

let processAge = {age ->
  if age < 0 then error("Age cannot be negative")
  else if age > 150 then error("Hmmm, your age seems unrealistic")
  else format("Age {} is valid", age)
} in processAge(25)
```

### Conditional Assignment

```numfu
let status = {score ->
  if score >= 90 then "excellent"
  else if score >= 70 then "good"
  else if score >= 50 then "pass"
  else "fail"
} in status(85)  // "good"
```
