# Special Operators

NumFu includes several expressive operators to make functional programming more intuitive:

- `>>` for **function composition**
- `|>` for **data piping**
- `...` for **list spreading and rest arguments**

-----
## Function Composition (`>>`)

Function composition lets you build new functions by chaining simpler ones together.

```numfu
let add1 = {x -> x + 1} in
let double = {x -> x * 2} in
let add1ThenDouble = add1 >> double in
  add1ThenDouble(5)           // 12  ((5 + 1) * 2)
````

You can chain as many functions as needed:

```numfu
import * from "std"

let capitalize = {s -> toUpperCase(s[0]) + slice(s, 1, -1)} in
let clean = trim >> toLowerCase >> capitalize in
  clean("  HELLO WORLD  ")    // "Hello World"
```

-----
## Piping (`|>`)

Piping is about applying a series of functions to a value. It passes the result of one expression as argument to the next function:

```numfu
5 |> {x -> x + 1} |> {x -> x * 2}   // 12
```

This is equivalent to:

```numfu
{ x -> x * 2 }({ x -> x + 1 }(5))
```

Piping makes data processing chains more readable and expressive

```numfu
import format from "std"

let isEven = {x -> x % 2 == 0} in
let double = {x -> x * 2} in
let halve = {x -> x / 2} in
  6 |> {x -> if isEven(x) then double(x) else halve(x)}
  |> {x -> format("Result: {}", x)}
```
```
Result: 12
```

-----
## Composition vs Piping

**Function Composition (`>>`)** creates a *new* function:

```numfu
let f = {x -> x + 1} >> {x -> x * 2} in
f(5)    // 12
```

**Piping (`|>`)** applies functions *immediately*:

```numfu
5 |> {x -> x + 1} |> {x -> x * 2}    // 12
```


-----
## Currying + Composition

Currying lets you fix arguments before composing:

```numfu
let add = {x, y -> x + y} in
let multiply = {x, y -> x * y} in

let pipeline = add(10) >> multiply(2) in
pipeline(5)                  // 30  ((5 + 10) * 2)
```


-----
## Spread Operator (`...`)

The spread operator unpacks list elements or [collects extra arguments](http://localhost:3000/docs/guide/functions#collecting-extra-arguments).


### List Spreading

Use `...` inside lists to insert the contents of other lists:

```numfu
[1, ...[2, 3], 4];            // [1, 2, 3, 4]
[...[1, 2], ...[3, 4]];       // [1, 2, 3, 4]
```

Spreading is especially useful when combining multiple variables:

```numfu
let a = [1, 2], b = [3, 4], c = [5, 6] in
  [0, ...a, ...b, ...c, 7]   // [0, 1, 2, 3, 4, 5, 6, 7]
```

Empty lists are ignored when spread:

```numfu
[1, ...[], 2];                // [1, 2]
[...[], ...[]];               // []
```

### Spread in Function Calls and Parameters

`...` can be used to collect or expand arguments in functions.

For *collecting* arguments, [see here](functions#rest-parameters).

As within lists, you can use the spread operator inside function calls to *expand* arguments:
```numfu
import log from "math"

let args = [64, 2] in
  log(...args)    // same as log(64, 2) -> 6
```
