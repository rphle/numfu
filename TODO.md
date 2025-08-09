### Import/Export System
a.nfu:

```
export func, my_var
```

b.nfu:
```
import func, my_var from a
```


### Syntax Highlighting
Syntax highlighting and editor support, mainly using [tree-sitter](https://tree-sitter.github.io/tree-sitter/)

### "Delete last output" Function
`del()` function that removes the last printed text from stdout (all printed values are collected in the `output` list in the interpreter)

### Dot Operator
Cool syntactic sugar for cleaner code and to emulate object orientied concepts:

```
// Using 'EXPR.CALL(args)', the expression before the dot is the first argument to the function
// e.g.:
"i like cheese".split(" ")
// is the same as:
split("i like cheese", " ")
// but looks way better
```

### While Loop
Currently, loops are only possible with recursion. Some while loop syntax which essentially desugares to recursion but can be handled better and faster by the interpreter is definitely needed.

### Lambda comparisons
Implement proper rules to determine the equality of two functions

### Builtin Function Partial Application
Make built-ins like `join` also return partially applied functions instead of raising errors if not enough arguments were given.

### "Delay" Arguments
If you use `_` in a function call, another function that still requires these arguments is returned:

```
map(_, {x -> x+1})
// returns
{a -> map(a, {x -> x+1})}
```
