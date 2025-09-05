# Printing and Assertions

NumFu offers simple tools for debugging and verification. Use `print`, `println`, `assert`, or sugar syntax to check results and trace execution.

-----

## Printing Output

Use `print` and `println` for output. All values are automatically converted to strings.

```numfu
print("I like cheese")
print(" and tomatoes.\n")

println("They are indeed very delicious.")
```

**Output:**

```
I like cheese and tomatoes.
They are indeed very delicious.
```

`println(x)` is equivalent to `print(x + "\n")`.

---

## Assertions

Use assertions to validate that values match expectations. They throw an error if the condition fails.

### Basic Form

```numfu
// Assert boolean condition
assert(2 + 2 == 4)

// Optional return value for use in expressions
let greet = {name -> "Hello " + assert(length(name) == 5, name)}

greet("James")
greet("Mary")
```

**Output:**

```
true
Hello James
...
AssertionError
```
-----

### Syntactic Sugar

Top-level expressions can use the `--->` operator for readable assertions.

```numfu
2 + 2 ---> $ == 4             // same as assert(2 + 2 == 4)
length("hello") ---> $ == 5
```

* `$` refers to the expression on the left
* This form is **only valid at top-level**, not inside functions

-----

## Errors

Use `error(message)` to stop execution with a custom message.

```numfu
let divide = {a, b ->
  if b != 0 then a / b
  else error("Cannot divide by zero!")
} in
  divide(42, 0)

// RuntimeError: Cannot divide by zero!
```

You can also specify a custom error name:

```numfu
error("Cannot divide by zero!", "MathError")

// MathError: Cannot divide by zero!
```
