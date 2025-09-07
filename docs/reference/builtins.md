# Built-ins

NumFu comes with a set of built-in constants and operators that are always available in every program. Most operators are overloaded to work with different types.

-----
## Constants

Mathematical and special constants available globally.

-----
### `nan`
**Type**: `Number`

**Description**: Not a Number (represents undefined mathematical results)

```numfu
nan                // nan
0 / 0              // nan
sqrt(-1)           // nan
```

-----
### `inf`
**Type**: `Number`

**Description**: Positive infinity

```numfu
inf                 // inf
1 / 0               // inf
-1 / 0              // -inf
```

-----
## Functional Operations

-----
### `map(list, function)`
**Parameters**: `List, Lambda`

**Returns**: `List` - new list with function applied to each element

```numfu
map([1, 2, 3, 4], {x -> x * x})     // [1, 4, 9, 16]
map(["hello", "world"], length)     // [5, 5]
map([1, 2, 3], {x -> x + 10})       // [11, 12, 13]
```

-----
### `filter(list, predicate)`
**Parameters**: `List, Lambda`

**Returns**: `List` - new list with elements that satisfy predicate

```numfu
filter([1, 2, 3, 4, 5], {x -> x % 2 == 0})                    // [2, 4]
filter(["apple", "banana", "cherry"], {s -> length(s) > 5})   // ["banana", "cherry"]
```

-----
## System Functions

-----
### `error(message)`, `error(message, type)`
**Parameters**: `String` or `String, String`

**Returns**: Never returns (throws error)

```numfu
error("Something went wrong")
error("Invalid input", "ValueError")
```

-----
### `assert(condition)`, `assert(condition, return)`
**Parameters**: `Boolean` or `Boolean, Any`

**Returns**: `Boolean | Any` - true or the return value if condition is true

Throws assertion error if condition is false.

```numfu
assert(2 + 2 == 4)                // Passes
assert(2 + 2 == 5, "Math error")  // Fails with message
```

-----
### `exit()`
**Parameters**: None

**Returns**: Never returns (exits program)

-----
## Arithmetic Operators

-----
### `+` (Addition)
**Overloads**:
- `Number + Number → Number`
- `String + String → String`
- `List + List → List`

```numfu
5 + 3                      // 8
"Hello" + " " + "World";   // "Hello World"
[1, 2] + [3, 4]            // [1, 2, 3, 4]
```

-----
### `-` (Subtraction)
**Overloads**:
- `Number → Number` (unary negation)
- `Number - Number → Number`

```numfu
-5                  // -5
10 - 3              // 7
5 - 8               // -3
```

-----
### `*` (Multiplication)
**Overloads**:
- `Number * Number → Number`
- `String * Number → String`
- `List * Number → List`

**Commutative**: String/List multiplication works in both orders.

```numfu
5 * 3               // 15
"Ha" * 3            // "HaHaHa"
3 * "Ho";           // "HoHoHo"
[1, 2] * 3          // [1, 2, 1, 2, 1, 2]
```

-----
### `/` (Division)
**Overloads**:
- `Number / Number → Number`

**Special cases**:
- Division by zero returns `inf` or `-inf`
- `0 / 0` returns `nan`

```numfu
10 / 2              // 5
1 / 0               // inf
-1 / 0              // -inf
0 / 0               // nan
```

-----
### `%` (Modulo)
**Overloads**:
- `Number % Number → Number`

```numfu
10 % 3              // 1
7 % 2               // 1
8 % 4               // 0
```

-----
### `^` (Exponentiation)
**Overloads**:
- `Number ^ Number → Number`

```numfu
2 ^ 8               // 256
3 ^ 2               // 9
4 ^ 0.5             // 2 (square root)
```

-----
## Logical Operators

-----
### `&&` (Logical AND)
**Overloads**:
- `Any && Any → Boolean`

**Short-circuiting**: If first operand is falsy, second is not evaluated.

```numfu
true && false             // false
true && true              // true
false && sqrt("error")    // false (doesn't evaluate sqrt)
5 && 0                    // false
```

-----
### `||` (Logical OR)
**Overloads**:
- `Any || Any → Boolean`

**Short-circuiting**: If first operand is truthy, second is not evaluated.

```numfu
true || false             // true
false || false            // false
true || sqrt("error")     // true (doesn't evaluate sqrt)
0 || 5                    // true
```

-----
### `!` (Logical NOT)
**Overloads**:
- `!Any → Boolean`

```numfu
!true               // false
!false              // true
!0                  // true
!5                  // false
!""                 // true
!"hello"            // false
```

-----
### `xor` (Logical XOR)
**Overloads**:
- `xor(Any, Any) → Boolean`

```numfu
xor(true, false)    // true
xor(true, true)     // false
xor(false, false)   // false
xor(1, 0)           // true
```

-----
## Comparison Operators

-----
### `==` (Equality)
**Overloads**:
- `Any == Any → Boolean`

```numfu
5 == 5              // true
"hello" == "hello"; // true
[1, 2] == [1, 2]    // true
5 == "5"            // false
```

-----
### `!=` (Inequality)
**Overloads**:
- `Any != Any → Boolean`

```numfu
5 != 3              // true
"a" != "b";         // true
[1, 2] != [2, 1]    // true
```

-----
### `>` (Greater Than)
**Overloads**:
- `Number > Number → Boolean`


-----
### `<` (Less Than)
**Overloads**:
- `Number < Number → Boolean`


-----
### `>=` (Greater Than or Equal)
**Overloads**:
- `Number >= Number → Boolean`


-----
### `<=` (Less Than or Equal)
**Overloads**:
- `Number <= Number → Boolean`
