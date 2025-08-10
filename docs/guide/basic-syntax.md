---
sidebar_position: 1
---

# Basic Syntax

This is a quick overview on the structure of NumFu programs.

-----
## Basic Program
 A NumFu program consists of expressions and optional assertions

```numfu
42                      // Simple expression
println("Hello!")       // Function call
let x = 5 in x * 2      // Let binding
sqrt(25) ---> $ == 5    // Assertion
```
```
42
Hello!
10
5
```

Every expression is evaluated and the result is written to stdout. For information on the separation of expressions, see below.

-----
## Expression Termination
Semicolons (`;`) mark the definitive end of an expression. They *can* be omitted but are highly advised in more complex programs since they prevent unexpected bugs like this, because NumFu generally ignores whitespace and newlines:

```numfu
42          //Number
[1,2,3,4]   // List
```
```
[at REPL:2:1]
[2]   [1]   // List
      ^^^
TypeError: 'Number' object is not subscriptable
```
NumFu identified the list as index for the previous expression.

-----
## Comments

### Single-line Comments
```numfu
// This is a single-line comment
1+1       // End-of-line comment
```

### Multi-line Comments
```numfu
/*
   This is a multi-line comment
   that can span several lines
   and is useful for longer explanations
*/
```

-----
## Operator Precedence

From highest to lowest precedence:

1. **Parentheses**: `()`
2. **Function calls**: `f(x)`, Indexing: `a[i]`
3. **Exponentiation**: `^` (right-associative)
4. **Unary operators**: `+`, `-`, `!`
5. **Multiplication, Division, Modulo**: `*`, `/`, `%`
6. **Addition, Subtraction**: `+`, `-`
7. **Comparison**: `<`, `>`, `<=`, `>=`
8. **Equality**: `==`, `!=`
9. **Logical AND**: `&&`
10. **Logical OR**: `||`
11. **Composition**: `>>`
12. **Pipe**: `|>`

```numfu
2 + 3 * 4            // 14
2^3^2                // 512 (2^(3^2), right-associative)
!true && false       // false ((!true) && false)
1 < 2 == true        // true ((1 < 2) == true)
x |> f >> g          // x |> (f >> g) (composition before pipe)
```

-----
## Associativity Rules

### Left-associative Operators
```numfu
10 - 5 - 2           // 3 ((10 - 5) - 2)
12 / 4 / 3           // 1 ((12 / 4) / 3)
1 < 2 < 3            // true ((1 < 2) && (2 < 3))
```

### Right-associative Operators
```numfu
2^3^2                // 512 (2^(3^2))
f >> g >> h          // f >> (g >> h)
```

-----
## Reserved Words

The following words are reserved and cannot be used as identifiers (it does not immediately raise errors if you use them e.g. as variable names but you won't get very far):

- `let`
- `in`
- `const`
- `if`
- `then`
- `else`
- `true`
- `false`

-----
## Identifier Rules

### Valid Identifiers
```numfu
// Letters, numbers, underscores
myVariable
_private
camelCase
snake_case
var123
_123
```

### Invalid Identifiers
```numfu
// Cannot start with numbers
123var

// No unicode letters
αβγ
变量

// Cannot contain special characters
my-var
my@var
my var
```
