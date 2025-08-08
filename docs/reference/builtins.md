---
sidebar_position: 1
---

# Built-ins

NumFu comes with a comprehensive set of built-in constants and functions covering mathematics, string manipulation, list operations, and more. All functions are overloaded to work with appropriate types and provide helpful error messages.

-----
## Constants

Mathematical and special constants available globally.

-----
### `pi`
**Type**: `Number`

**Description**: Mathematical constant π (pi)

**Value**: `3.14159265358979323846...`

-----
### `e`
**Type**: `Number`

**Description**: Euler's number (base of natural logarithm)

**Value**: `2.71828182845904523536...`

-----
### `nan`
**Type**: `Number`

**Description**: Not a Number (represents undefined mathematical results)

```numfu
nan                 // nan
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

-----
## Mathematical Functions

### Trigonometric Functions

-----
#### `sin(x)`
**Parameters**: `Number` - angle in radians

**Returns**: `Number` - sine of x

-----
#### `cos(x)`
**Parameters**: `Number` - angle in radians

**Returns**: `Number` - cosine of x

-----
#### `tan(x)`
**Parameters**: `Number` - angle in radians

**Returns**: `Number` - tangent of x

-----
#### `asin(x)`, `acos(x)`, `atan(x)`
**Parameters**: `Number` - value

**Returns**: `Number` - inverse trig function result in radians

-----
#### `atan2(y, x)`
**Parameters**: `Number, Number` - y and x coordinates

**Returns**: `Number` - angle in radians from x-axis to point (x,y)

-----
### Hyperbolic Functions

-----
#### `sinh(x)`, `cosh(x)`, `tanh(x)`
**Parameters**: `Number`

**Returns**: `Number` - hyperbolic sine, cosine, or tangent

-----
#### `asinh(x)`, `acosh(x)`, `atanh(x)`
**Parameters**: `Number`

**Returns**: `Number` - inverse hyperbolic function


-----
### Exponential and Logarithmic Functions

-----
#### `exp(x)`
**Parameters**: `Number`

**Returns**: `Number` - e raised to the power x

-----
#### `log(x, base)`
**Parameters**: `Number, Number` - value and base

**Returns**: `Number` - logarithm of x in given base

-----
#### `log10(x)`
**Parameters**: `Number`

**Returns**: `Number` - base-10 logarithm

-----
#### `sqrt(x)`
**Parameters**: `Number`

**Returns**: `Number` - square root

-----
### Rounding and Comparison Functions

-----
#### `ceil(x)`
**Parameters**: `Number`

**Returns**: `Number` - smallest integer ≥ x

-----
#### `floor(x)`
**Parameters**: `Number`

**Returns**: `Number` - largest integer ≤ x

-----
#### `round(x)`, `round(x, precision)`
**Parameters**: `Number` or `Number, Number`

**Returns**: `Number` - rounded value

-----
#### `sign(x)`
**Parameters**: `Number`

**Returns**: `Number` - -1, 0, or 1

```numfu
sign(5)             // 1
sign(-3)            // -1
sign(0)             // 0
```

-----
#### `abs(x)`
**Parameters**: `Number`

**Returns**: `Number` - absolute value

-----
#### `max(...numbers)`, `max(list)`
**Parameters**: Variable numbers or a list

**Returns**: `Number` - maximum value

```numfu
max(1, 5, 3, 9, 2)  // 9
max([1, 5, 3, 9, 2]) // 9
```

-----
#### `min(...numbers)`, `min(list)`
**Parameters**: Variable numbers or a list

**Returns**: `Number` - minimum value

```numfu
min(1, 5, 3, 9, 2)  // 1
min([1, 5, 3, 9, 2]) // 1
```

-----
## Type Conversion Functions

-----
### `Bool(x)`
**Parameters**: `Any`

**Returns**: `Boolean` - boolean representation

**Falsy values**: `false`, `0`, `""`, `[]`

**Truthy values**: Everything else

```numfu
Bool(1)             // true
Bool(0)             // false
Bool("hello")       // true
Bool("")            // false
Bool([1, 2])        // true
Bool([])            // false
```

-----
### `Number(x)`
**Parameters**: `Boolean | Number | String`

**Returns**: `Number` - numeric representation

```numfu
Number(true)        // 1
Number(false)       // 0
Number("42")        // 42
Number("3.14")      // 3.14
Number("hello")     // Error: Can't convert to number
```

-----
### `List(x)`
**Parameters**: `Any` (must be iterable)

**Returns**: `List` - list representation

```numfu
List("hello")       // ["h", "e", "l", "l", "o"]
List([1, 2, 3])     // [1, 2, 3]
```

-----
### `String(x)`
**Parameters**: `Any`

**Returns**: `String` - string representation

```numfu
String(42)          // "42"
String(true)        // "true"
String([1, 2, 3])   // "[1, 2, 3]"
```

-----
## List and String Operations

### List Operations

-----
#### `append(list, element)`
**Parameters**: `List, Any`

**Returns**: `List` - new list with element added at end

```numfu
append([1, 2, 3], 4)        // [1, 2, 3, 4]
append([], "first")         // ["first"]
```

-----
#### `length(list)`, `length(string)`
**Parameters**: `List | String`

**Returns**: `Number` - number of elements/characters

```numfu
length([1, 2, 3, 4])        // 4
length("hello")             // 5
length([])                  // 0
```

-----
#### `contains(list, element)`, `contains(string, substring)`
**Parameters**: `List, Any` or `String, String`

**Returns**: `Boolean` - true if element is found

```numfu
contains([1, 2, 3], 2 )     // true
contains("hello", "lo")     // true
contains([1, 2, 3], 4)      // false
```

-----
#### `set(list, index, value)`, `set(string, index, char)`
**Parameters**: `List, Number, Any` or `String, Number, String`

**Returns**: `List | String` - new collection with element changed

```numfu
set([1, 2, 3], 1, 99)       // [1, 99, 3]
set("hello", 0, "H")        // "Hello"
```

-----
#### `reverse(list)`, `reverse(string)`
**Parameters**: `List | String`

**Returns**: `List | String` - reversed collection

```numfu
reverse([1, 2, 3, 4])       // [4, 3, 2, 1]
reverse("hello")            // "olleh"
```

-----
#### `sort(list)`, `sort(string)`
**Parameters**: `List | String`

**Returns**: `List | String` - sorted collection

```numfu
sort([3, 1, 4, 1, 5])       // [1, 1, 3, 4, 5]
sort("dcba")                // "abcd"
```

-----
#### `slice(collection, start, end)`
**Parameters**: `List | String, Number, Number`

**Returns**: `List | String` - slice from start to end (inclusive)

Use `-x` for end to go to the end of the collection.

```numfu
slice([1, 2, 3, 4, 5], 1, 3)    // [2, 3, 4]
slice("hello", 1, 3)            // "ell"
slice([1, 2, 3, 4, 5], 2, -2)   // [3, 4]
```

-----
### String-Specific Operations

-----
#### `join(list, separator)`
**Parameters**: `List<String>, String`

**Returns**: `String` - elements joined with separator

```numfu
join(["hello", "world"], "-")   // "hello-world"
join([], ",")                   // ""
```

-----
#### `split(string, delimiter)`
**Parameters**: `String, String`

**Returns**: `List` - string split by delimiter

```numfu
split("hello,world", ",")       // ["hello", "world"]
split("one two three", " ")     // ["one", "two", "three"]
split("hello", "")              // ["hello"]
```

-----
#### `format(template, ...args)`
**Parameters**: `String, ...String`

**Returns**: `String` - formatted string

Use `{}` as placeholders in the template.

```numfu
format("Hello, {}!", "World")               // "Hello, World!"
format("{} + {} = {}", "2", "3", "5")       // "2 + 3 = 5"
format("Name: {}, Age: {}", "Alice", "30")  // "Name: Alice, Age: 30"
```

-----
#### `trim(string)`
**Parameters**: `String`

**Returns**: `String` - string with leading and trailing whitespace removed
```numfu
trim("  hello  ")       // "hello"
```
-----
#### `toLowerCase(string)`
**Parameters**: `String`

**Returns**: `String` - string in lowercase
```numfu
toLowerCase("HELLO")    // "hello"
```
-----
#### `toUpperCase(string)`
**Parameters**: `String`

**Returns**: `String` - string in uppercase
```numfu
toUpperCase("hello")    // "HELLO"
```
-----
#### `replace(string, old, new)`
**Parameters**: `String, String, String`

**Returns**: `String` - string with occurrences of old replaced by new
```numfu
replace("hello world", "world", "there") // "hello there"
```
-----
#### `count(string, substring)`
**Parameters**: `String, String`

**Returns**: `Number` - count of occurrences of substring in string
```numfu
count("hello hello", "hello") // 2
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
## Output Functions

-----
### `print(value)`
**Parameters**: `Any`

**Returns**: `Any` - the input value (for chaining)

Prints the value without a newline.

```numfu
print("Hello")      // Prints: Hello
print(42)           // Prints: 42
```

-----
### `println(value)`
**Parameters**: `Any`

**Returns**: `Any` - the input value (for chaining)

Prints the value with a newline.

```numfu
println("Hello")    // Prints: Hello\n
println(42)         // Prints: 42\n
```

-----
## Random Functions

-----
### `random()`
**Parameters**: None

**Returns**: `Number` - random number between 0 and 1

```numfu
random()                  // 0.7234567891234567 (example)
random() * 10             // Random number 0-10
floor(random() * 6) + 1   // Random dice roll 1-6
```

-----
### `seed(value)`
**Parameters**: `Number | String`

**Returns**: `None` - seeds the random number generator

```numfu
seed(42)            // Set seed for reproducible randomness
seed("hello")       // Can also use strings as seeds
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
### `time()`
**Parameters**: None

**Returns**: `Number` - current Unix timestamp
