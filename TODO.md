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

### Lambda comparisons
Implement proper rules to determine the equality of two functions

### Builtin Function Partial Application
Make built-ins like `join` also return partially applied functions instead of raising errors if not enough arguments were given. You can also just use _ placeholders but this would be more intuitive and similar in behavior to user-defined functions.
