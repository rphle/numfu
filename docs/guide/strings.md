# Strings and Text

NumFu treats text as first-class data with powerful string operations. Let's explore how to work with strings in NumFu.

-----
## String Literals

### Basic Strings

Strings are enclosed in double quotes:

```numfu
"Hello, NumFu!"
"Programming is fun"
""                        // Empty string
```

### Escape Sequences

Use backslash for special characters:

```numfu
"Line 1\nLine 2"          // Newline
"Tab\tSeparated"          // Tab character
"Quote: \"Hello\""        // Escaped quotes
"Backslash: \\"           // Escaped backslash
"Unicode: \u03B1"         // Unicode (α)
```

-----
## String Operations

Strings are very similar to lists and share many operations with them. You can think of them as lists of characters.

### Concatenation

Join strings with the `+` operator:

```numfu
"Hello" + " " + "World"     // "Hello World"
"NumFu" + "!"               // "NumFu!"

// Multi-line concatenation
"This is a very long string " +
"that spans multiple lines"
```

### Repetition

Repeat strings with the `*` operator:

```numfu
3 * "Ho"             // "HoHoHo"
"=" * 20             // "===================="
2* "NumFu "          // "NumFu NumFu "
```

-----
## String Access and Properties

### Character Indexing

Access individual characters with square brackets ([just like elements in a list](http://localhost:3000/docs/guide/lists#accessing-list-elements)):

```numfu
"Hello"[0]           // "H" (first character)
"Hello"[4]           // "o" (last character)
"NumFu"[2]           // "m"
```

### Negative Indexing

Count from the end with negative indices:

```numfu
"Hello"[-1]          // "o" (last character)
"Hello"[-2]          // "l" (second to last)
"Programming"[-1]    // "g"
```


-----
## String Properties & Functions

### String Length

```numfu
length("Hello")          // 5
length("")               // 0
length("NumFu rocks!")   // 12
```

### Case Conversion

```numfu
toLowerCase("HELLO")     // "hello"
toUpperCase("world")     // "WORLD"
```

### String Testing

```numfu
contains("hello", "lo")    // true (substring exists)
contains("hello", "xyz")   // false
```

### Count Substrings

```numfu
count("The math is not mathing.", "math")
// 2 (two occurences of "math")
```

### String Slicing

Extract substrings using `slice(string, start, end)`:

```numfu
slice("Hello World", 0, 4)    // "Hello"
slice("Programming", 3, 6)    // "gram"
slice("NumFu", 1, -1)         // "umF" (from index 1 to end-1)
```

### Splitting Strings

Split a string into a list of strings by the specified separator: `split(string, separator)`

```numfu
let text = "NumFu Programming Language" in
let words = split(text, " ") in
  words // ["NumFu", "Programming", "Language"]
```

### Joining Lists

Join a list of strings with a separator: `join(list, separator)`

```numfu
let words = ["NumFu", "Programming", "Language"] in
  join(words, "-")     // "NumFu-Programming-Language"
```

-----
## Template Strings & Formatting

The `format()` function allows you to create formatted strings by inserting values into placeholders. It takes a string and the same number of additional arguments as there are placeholders (`{}`).

```numfu
format("Welcome to {}, {}!", "NumFu", "programmer")
// "Welcome to NumFu, programmer!"

format("Result: {} + {} = {}", 2, 3, 5)
// "Result: 2 + 3 = 5"
```

If you do not supply the correct number of arguments, an `IndexError` will be raised.

```numfu
format("{} likes {}", "John")
// IndexError: Incorrect number of placeholders
```

### Escape placeholders

To escape placeholders and treat them as literal characters, enclose them in curly braces

```numfu
format("Using placeholders {{}}, you can format {}", "strings")
// "Using placeholders {}, you can format strings"
```

-----
## Examples

### Bordered Title

```numfu
let border = "=" * 50 in
let title = "NumFu Tutorial" in
let padding = ((50 - length(title)) / 2) in
  border + "\n" +
  " " * padding + title + "\n" +
  border
```
```
==================================================
                  NumFu Tutorial
==================================================
```

### Building Messages

```numfu
let name = "Alice" in
let age = 30 in
  "Hello, " + name + "! You are " + String(age) + " years old."
// Hello, Alice! You are 30 years old.
```

### String Validation

```numfu
{isValidEmail: email ->
  if count(email, "@") != 1 then false else
    let splitted = split(email, "@") in
      count(splitted[1], ".") > 0
      && splitted[1][-1] != "."
      && splitted[0][0] != "."
}

isValidEmail("user@example.com")        // true
isValidEmail("userexample.com")         // false
isValidEmail("user@email@example.com")  // false
isValidEmail("user@example.com.")       // false
```

### String Processing

Take a list of boolean options to determine whether to trim, lowercase, and replace spaces with underscores in the input text.

```numfu
// Text processor factory
{makeTextProcessor: options ->
  let shouldTrim = options[0],
      shouldLower = options[1],
      shouldReplace = options[2] in
    {text ->
      let step1 = if shouldTrim then trim(text) else text in
      let step2 = if shouldLower then toLowerCase(step1) else step1 in
      let step3 = if shouldReplace then replace(step2, " ", "_") else step2 in
        step3
    }
}

let processor = makeTextProcessor([true, true, true]) in
  processor("  Hello World  ")    // "hello_world"
```
