---
sidebar_position: 6
---

# Lists

Lists are NumFu's primary data structure for working with collections of values. They're immutable, heterogeneous (can contain different types), and come with powerful operations for transformation and manipulation.

-----
## Creating Lists

### List Literals

Create lists using square brackets with comma-separated elements:

```numfu
[];                             // Empty list
[1, 2, 3];                      // Numbers
["hello", "world"];             // Strings
[true, false, true];            // Booleans
[1, "hello", true];             // Mixed types
```

### Nested Lists

Lists can contain other lists:

```numfu
[[1, 2], [3, 4]];               // 2D list
[[], [1], [1, 2]];              // Lists of different lengths
[[[1]], [[2, 3]], [[4, 5, 6]]]; // 3D nested structure
```

### Lists with Expressions

List elements can be any expressions:

```numfu
[1 + 2, 3 * 4, 5^2];            // [3, 12, 25]
[sin(0), cos(0), tan(0)];       // [0, 1, 0]

let x = 10 in [x, x*2, x*3];    // [10, 20, 30]
```

-----
## Accessing List Elements

### Indexing

Access elements using square bracket notation (0-based indexing):

```numfu
let fruits = ["apple", "banana", "cherry"] in
  fruits[0];    // "apple"
  // or...
  fruits[1];    // "banana"
  fruits[2];    // "cherry"
```

### Negative Indexing

Access elements from the end using negative indices:

```numfu
let numbers = [10, 20, 30, 40, 50] in
  numbers[-1];    // 50 (last element)
  // or...
  numbers[-2];    // 40 (second to last)
```

### Nested List Access

Access nested lists by chaining indices:

```numfu
let matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]] in
  matrix[1][2];    // 6 (row 1, column 2)
  // or...
  matrix[0][0];    // 1 (top-left)
  matrix[2][2];    // 9 (bottom-right)
```

### Index Bounds

Accessing out-of-bounds indices raises an error:

```numfu
let short = [1, 2] in
  short[5]
// IndexError: List index out of range
```

-----
## List Operations

### Concatenation

Combine lists using the `+` operator:

```numfu
[1, 2] + [3, 4];                // [1, 2, 3, 4]
["a"] + ["b", "c"] + ["d"];     // ["a", "b", "c", "d"]
[] + [1, 2, 3];                 // [1, 2, 3]
```

### Repetition

Repeat lists using the `*` operator:

```numfu
[1, 2] * 3;                     // [1, 2, 1, 2, 1, 2]
["hello"] * 2;                  // ["hello", "hello"]
[1, 2, 3] * 0;                  // []
```

### List Equality

Compare lists for equality:

```numfu
[1, 2, 3] == [1, 2, 3];         // true
[1, 2] == [2, 1];               // false (order matters)
[] == [];                       // true
```

-----
## Built-in List Functions

### Length

```numfu
length([1, 2, 3, 4]);           // 4
length([]);                     // 0
```

### Adding Elements

```numfu
[1, 2, 3] + [4]                 // [1, 2, 3, 4]
append([1, 2, 3], 4);           // [1, 2, 3, 4]
append([], "first");            // ["first"]
```

### Element Testing

```numfu
contains([1, 2, 3], 2);           // true
contains(["a", "b", "c"], "x");   // false
contains([[], [1], [2]], []);     // true
```

### List Transformation

```numfu
reverse([1, 2, 3, 4]);          // [4, 3, 2, 1]
reverse([]);                    // []
reverse(["a", "b", "c"]);       // ["c", "b", "a"]
```

### Sorting

```numfu
sort([3, 1, 4, 1, 5]);                // [1, 1, 3, 4, 5]
sort(["banana", "apple", "cherry"]);  // ["apple", "banana", "cherry"]
```

### Slicing

Extract sublists using `slice(list, start, end)`:

```numfu
slice([1, 2, 3, 4, 5], 1, 3);   // [2, 3, 4] (inclusive end)
slice([1, 2, 3, 4, 5], 0, 2);   // [1, 2, 3]
slice([1, 2, 3, 4, 5], 2, -2);  // [3, 4] (negative index)
```

### Setting Elements

Create new lists with modified elements:

```numfu
set([1, 2, 3], 1, 99);          // [1, 99, 3]
set(["a", "b", "c"], 0, "X");   // ["X", "b", "c"]
```

-----
## Functional List Operations

### `map` - Transform Every Element

Apply a function to every element in a list:

```numfu
let numbers = [1, 2, 3, 4, 5] in
let squares = map(numbers, {x -> x * x}) in
  squares    // [1, 4, 9, 16, 25]
```

### `filter` - Select Elements

Keep only elements that satisfy a condition:

```numfu
let numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] in
let evens = filter(numbers, {x -> x % 2 == 0}) in
  evens    // [2, 4, 6, 8, 10]
```

-----
## Examples

### List Comprehension Style

While NumFu doesn't have list comprehensions, you can simulate them:

```numfu
// Generate even squares of numbers 1-10
let range = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] in
  filter(map(range, {x -> x * x}), {x -> x % 2 == 0})
// [4, 16, 36, 64, 100]
```

### Matrix Operations

#### Sum each row in a matrix
```numfu
let matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]] in
  map(matrix, {row ->
    let sum = {lst ->
      if length(lst) == 0 then 0
      else lst[0] + sum(slice(lst, 1, -1))
    } in sum(row)
  })
// [6, 15, 24]
```

#### Flatten a matrix
```numfu
let flatten = {lists ->
  if length(lists) == 0 then []
  else lists[0] + flatten(slice(lists, 1, -1))
} in
flatten([[1, 2], [3, 4], [5, 6]])
// [1, 2, 3, 4, 5, 6]
```

#### Transpose a matrix
```numfu
let transpose = {matrix ->
  if length(matrix) == 0 then []
  else
    let numCols = length(matrix[0]) in
    let getColumn = {col ->
      map(matrix, {row -> row[col]})
    } in
    let range = [0, 1, 2] in  // Assuming 3x3 matrix
      map(range, getColumn)
} in
transpose([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
// [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
```

### Statistics
#### Calculate mean of a list
```numfu
{mean: numbers ->
  let sum = {lst ->
    if length(lst) == 0 then 0
    else lst[0] + sum(slice(lst, 1, -1))
  } in
  sum(numbers) / length(numbers)
}
mean([10, 20, 30, 40, 50])            // 30
```

### Safe List Access

```numfu
// Safe indexing with default values
{safeGet: lst, index, default ->
  if index >= 0 && index < length(lst) then lst[index]
  else default
};
safeGet([1, 2, 3], 5, 0);             // 0 (default)
safeGet([1, 2, 3], 1, 0);             // 2 (actual value)
```

### List Validation

```numfu
// Check if all elements satisfy a condition
{allPositive: numbers ->
  length(filter(numbers, {x -> x > 0})) == length(numbers)
}
allPositive([1, 2, 3, 4]);            // true
allPositive([1, -2, 3, 4]);           // false
```

### List Reduction

```numfu
{reduce: lst, fn, initial ->
  if length(lst) == 0 then initial
  else reduce(slice(lst, 1, -1), fn, fn(initial, lst[0]))
}
reduce([1, 2, 3, 4], {acc, x -> acc + x}, 0);  // 10
reduce([1, 2, 3, 4], {acc, x -> acc * x}, 1);  // 24
```
