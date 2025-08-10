# Numbers and Arithmetic

NumFu's foundation is built on powerful numeric computation with arbitrary precision arithmetic. Let's start with the basics of numbers and mathematical operations.

-----
## Number Literals

### Basic Numbers

NumFu supports several number formats:

```numfu
42;          // Integer
3.14159      // Decimal
.5           // Leading decimal point optional
-17          // Negative numbers
```

### Scientific Notation

For very large or small numbers:

```numfu
2.5e10       // 25,000,000,000
1.23E-4      // 0.000123
-1.5e6       // -1,500,000
```

-----
## Arithmetic Operators

### Basic Operations

```numfu
10 + 5       // Addition: 15
10 - 5       // Subtraction: 5
10 * 5       // Multiplication: 50
10 / 5       // Division: 2
10 % 3       // Modulo: 1
2 ^ 8        // Exponentiation: 256
```

### Unary Operators

```numfu
-42          // Negation: -42
+42          // Explicit positive: 42
--42         // Double negative: 42
```

-----
## Operator Precedence

NumFu follows mathematical precedence rules:

```numfu
2 + 3 * 4;           // 14 (multiplication first)
2 + 3 * 4^2;         // 50 (exponentiation first)
(2 + 3) * 4;         // 20 (parentheses override)
```

You can find more information [here](#operator-precedence).

-----
## Mathematical Constants

NumFu provides essential mathematical constants:

```numfu
pi;           // π ≈ 3.14159...
e;            // Euler's number ≈ 2.71828...
inf;          // Infinity
nan;          // Not a Number
```

-----
## Infinity and NaN

NumFu implements full Inf/NaN (not a number) arithmetic according to the [IEEE 754 standard](https://en.wikipedia.org/wiki/IEEE_754):

```numfu
1 / 0;        // +inf (positive infinity)
-1 / 0;       // -inf (negative infinity)
0 / 0;        // nan (not a number)
inf * 0       // nan
sqrt(-1)      // nan
nan > 42      // false
nan <= 42     // false
// ...
```

For a complete, easy-to-understand reference, see [this article](https://steve.hollasch.net/cgindex/coding/ieeefloat.html).

-----
## Examples

### Circle Area

```numfu
let radius = 5 in pi * radius^2  // 78.53...
```

### Quadratic Formula Discriminant

```numfu
let a = 1, b = 5, c = 6 in b^2 - 4*a*c  // 1
```

### Compound Interest

```numfu
let principal = 1000, rate = 0.05, years = 10 in
  principal * (1 + rate)^years  // 1628.89...
```
