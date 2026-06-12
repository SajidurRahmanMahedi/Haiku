# Haiku Programming Language

**Haiku** is a modern, expressive programming language designed to be **simpler than Python** while remaining powerful enough for real-world tasks. Haiku features clean syntax, f-strings for easy string interpolation, module imports, first-class functions, object-oriented programming, pattern matching, and a rich standard library.

## What's New in Haiku 2.0

- **F-strings**: Easy string interpolation with `f"Hello {name}"`
- **R-strings**: Raw strings for regex and paths with `r"C:\\path\\to\\file"`
- **Module imports**: Import custom `.hku` files and built-in modules
- **Simpler syntax**: Cleaner, more intuitive than Python
- **Error tracebacks**: Full call-stack traceback with exact line numbers on every runtime error
- **Unclosed comment detection**: `/* ... */` comments that are never closed now raise a clear `LexerError` instead of silently skipping code

- **File Extension**: `.hku`
- **Base Language**: Python (interpreter written in Python)
- **Paradigm**: Multi-paradigm (procedural, object-oriented, functional)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Language Syntax](#language-syntax)
3. [F-Strings & R-Strings](#f-strings--r-strings)
4. [Imports](#imports)
5. [Data Types](#data-types)
6. [Variables & Constants](#variables--constants)
7. [Operators](#operators)
8. [Control Flow](#control-flow)
9. [Functions](#functions)
10. [Object-Oriented Programming](#object-oriented-programming)
11. [Collections](#collections)
12. [Standard Library](#standard-library)
13. [Error Handling](#error-handling)
14. [Running Haiku](#running-haiku)
15. [Project Structure](#project-structure)
16. [Complete Example Programs](#complete-example-programs)

---

## Quick Start

```haiku
// Hello World in Haiku with f-strings
println("Hello, World!")

let name = "Haiku"
let version = 1.0

// Use f-strings for cleaner string interpolation
println(f"Language: {name}")
println(f"Version: {version}")
```

Run it:
```bash
python main.py hello.hku
```

Or use the interactive REPL:
```bash
python main.py
haiku> println(2 + 2)
4
```

---

## Language Syntax

### Comments
```haiku
// Single-line comment

/*
   Multi-line
   comment
*/
```

### Identifiers
- Must start with a letter or underscore
- Can contain letters, digits, and underscores
- Case-sensitive

### Keywords
```
let, const, fn, if, else, elif, for, while, return
class, this, super, import, from, as, true, false, none
and, or, not, try, catch, finally, throw, match, case
default, break, continue, in, async, await, yield
static, private, public
```

---

## F-Strings & R-Strings

### F-Strings (Formatted Strings)
F-strings provide an easy way to embed expressions inside string literals using curly braces.

```haiku
let name = "Alice"
let age = 30

// Simple interpolation
println(f"Hello, {name}!")
println(f"You are {age} years old")

// Expressions inside f-strings
println(f"Next year you'll be {age + 1}")

// Method calls
let text = "hello world"
println(f"Uppercase: {text.upper()}")

// Escaped braces
println(f"Literal braces: {{ and }}")
```

### R-Strings (Raw Strings)
R-strings treat backslashes as literal characters, perfect for regex patterns and file paths.

```haiku
// Regex pattern (no need to double-escape)
let pattern = r"\d+\w+"

// File paths (Windows-style)
let path = r"C:\Users\Documents\file.txt"

// Raw text with backslashes
let raw = r"Line 1\nLine 2\nLine 3"
println(raw)  // Prints: Line 1\nLine 2\nLine 3
```

---

## Imports

Haiku supports importing from custom `.hku` files and built-in modules.

### Import Built-in Modules
```haiku
// Import entire module
import Math
println(f"PI = {Math.PI}")
println(f"sqrt(16) = {Math.sqrt(16)}")

// Import Time module
import Time
let now = Time.now()
println(f"Timestamp: {now}")
```

### Import Custom .hku Files
```haiku
// Import from a custom file
import { greet, farewell } from 'my_module.hku'

greet("Alice")
farewell("Bob")

// Import entire module with alias
import 'utils.hku' as Utils
Utils.helperFunction()

// Import all exports
import * from 'helpers.hku'
```

### Creating Importable Modules
Create a file `my_module.hku`:
```haiku
// my_module.hku
let version = "1.0"

fn greet(name) {
    return f"Hello, {name}!"
}

fn farewell(name) {
    return f"Goodbye, {name}!"
}
```

Then import it in another file:
```haiku
import { greet, farewell, version } from 'my_module.hku'
println(greet("World"))
println(f"Module version: {version}")
```

---

## Data Types

### Primitive Types

| Type | Example | Description |
|------|---------|-------------|
| Number | `42`, `3.14` | Integers and floats |
| String | `"hello"`, `'world'` | Text with escape sequences |
| Boolean | `true`, `false` | Logical values |
| None | `none` | Absence of value |

```haiku
let count = 42
let price = 19.99
let message = "Hello"
let active = true
let empty = none
```

### Collection Types

**List** - ordered, mutable sequence:
```haiku
let fruits = ["apple", "banana", "cherry"]
let numbers = [1, 2, 3, 4, 5]
```

**Map** - key-value dictionary:
```haiku
let scores = {
    "alice": 95,
    "bob": 87,
    "charlie": 92
}
```

---

## Variables & Constants

```haiku
// Mutable variable
let name = "Alice"
name = "Bob"  // OK

// Immutable constant
const PI = 3.14159
// PI = 3.14  // ERROR!
```

Variables are block-scoped. Functions and classes create new scopes.

---

## Operators

### Arithmetic
```haiku
a + b    // Addition (also string concatenation, list concatenation)
a - b    // Subtraction
a * b    // Multiplication (also string repetition)
a / b    // Division
a % b    // Modulo
a ** b   // Power
```

### Comparison
```haiku
a == b   // Equal
a != b   // Not equal
a < b    // Less than
a > b    // Greater than
a <= b   // Less than or equal
a >= b   // Greater than or equal
```

### Logical
```haiku
a && b   // Logical AND (short-circuit)
a || b   // Logical OR (short-circuit)
!a       // Logical NOT
not a    // Alternative NOT
```

### Bitwise
```haiku
a & b    // Bitwise AND
a | b    // Bitwise OR
a ^ b    // Bitwise XOR
a << b   // Left shift
a >> b   // Right shift
~a       // Bitwise NOT
```

### Assignment
```haiku
a = b
a += b
a -= b
a *= b
a /= b
```

### Range
```haiku
1..5     // Creates [1, 2, 3, 4, 5]
```

### Ternary
```haiku
let status = age >= 18 ? "adult" : "minor"
```

### Optional Chaining
```haiku
obj?.property   // Returns none if obj is none instead of error
```

---

## Control Flow

### If / Elif / Else
```haiku
let score = 85

if score >= 90 {
    println("Grade: A")
} elif score >= 80 {
    println("Grade: B")
} elif score >= 70 {
    println("Grade: C")
} else {
    println("Grade: F")
}
```

### For Loop
```haiku
for i in range(1, 6) {
    println(i)
}

for fruit in ["apple", "banana", "cherry"] {
    println(fruit)
}

for key in {"a": 1, "b": 2} {
    println(key)
}
```

### While Loop
```haiku
let n = 5
let fact = 1
while n > 1 {
    fact = fact * n
    n = n - 1
}
println(f"5! = {fact}")
```

### Match (Pattern Matching)
```haiku
let day = "monday"
match day {
    "monday" => println("Start of week")
    "friday" => println("End of week")
    "saturday" => println("Weekend!")
    "sunday" => println("Weekend!")
    default => println("Midweek")
}
```

### Break & Continue
```haiku
for i in range(1, 10) {
    if i == 3 {
        continue
    }
    if i == 7 {
        break
    }
    println(i)
}
```

---

## Functions

### Function Declaration
```haiku
fn greet(name) {
    return f"Hello, {name}!"
}

println(greet("Haiku"))
```

### Default Parameters
```haiku
fn greetWithTitle(name, title = "Mr./Ms.") {
    return f"Hello, {title} {name}"
}

println(greetWithTitle("Smith"))        // Hello, Mr./Ms. Smith
println(greetWithTitle("Doe", "Dr."))   // Hello, Dr. Doe
```

### Lambda Functions
```haiku
let multiply = (a, b) => a * b
let square = (x) => x * x

println(multiply(4, 7))   // 28
println(square(5))        // 25
```

### Anonymous Functions
```haiku
let double = fn(x) {
    return x * 2
}
```

### Recursion
```haiku
fn factorial(n) {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}

println(factorial(5))  // 120
```

### Higher-Order Functions
```haiku
fn applyTwice(fn f, x) {
    return f(f(x))
}

let addTen = (x) => x + 10
println(applyTwice(addTen, 5))  // 25
```

### Closures
```haiku
fn makeCounter() {
    let count = 0
    return () => {
        count = count + 1
        return count
    }
}

let counter = makeCounter()
println(counter())  // 1
println(counter())  // 2
println(counter())  // 3
```

---

## Object-Oriented Programming

### Classes
```haiku
class Animal {
    fn init(name) {
        this.name = name
    }

    fn speak() {
        return f"{this.name} makes a sound"
    }
}

let animal = Animal("Creature")
println(animal.speak())
```

### Inheritance
```haiku
class Dog(Animal) {
    fn init(name, breed) {
        super.init(name)
        this.breed = breed
    }

    fn speak() {
        return f"{this.name} barks!"
    }

    fn info() {
        return f"{super.info()} ({this.breed})"
    }
}

let dog = Dog("Buddy", "Golden Retriever")
println(dog.speak())
println(dog.info())
println(f"Breed: {dog.breed}")
```

### Static Methods
```haiku
class Counter {
    static fn create() {
        return Counter()
    }
}

let c = Counter.create()
```

---

## Collections

### List Operations
```haiku
let nums = [1, 2, 3, 4, 5]

nums.push(6)           // Add to end
nums.pop()             // Remove from end
nums.shift()           // Remove from start
nums.unshift(0)        // Add to start

let first = nums.get(0)
nums.set(0, 10)

let hasThree = nums.contains(3)
let doubled = nums.map((x) => x * 2)
let evens = nums.filter((x) => x % 2 == 0)
let sum = nums.reduce((acc, x) => acc + x, 0)
let sorted = nums.sort()
let reversed = nums.reverse()
let joined = nums.join(", ")
let sliced = nums.slice(1, 3)

println(f"Length: {nums.len()}")
```

### Map Operations
```haiku
let scores = {"alice": 95, "bob": 87}

println(scores["alice"])
println(f"Keys: {scores.keys()}")
println(f"Values: {scores.values()}")
println(f"Entries: {scores.entries()}")
println(f"Has 'alice': {scores.has('alice')}")

scores.delete("bob")
scores.clear()
println(f"Length: {scores.len()}")
```

### String Methods
```haiku
let text = "  Hello, Haiku!  "

text.upper()
text.lower()
text.trim()
text.split(",")
text.contains("Haiku")
text.replace("Haiku", "World")
text.startsWith("Hello")
text.endsWith("!")
text.slice(0, 5)

text.len()
```

---

## Standard Library

### I/O Functions
```haiku
print("no newline")
println("with newline")

let name = input("Enter your name: ")
println(f"Hello, {name}")
```

### Type Functions
```haiku
type(value)     // Get type name as string
len(value)      // Get length of string/list/map
str(value)      // Convert to string
int(value)      // Convert to integer
float(value)    // Convert to float
bool(value)     // Convert to boolean
```

### Range
```haiku
range(5)        // [0, 1, 2, 3, 4]
range(1, 6)     // [1, 2, 3, 4, 5]
range(0, 10, 2) // [0, 2, 4, 6, 8]
```

### Math Module
```haiku
Math.PI
Math.E
Math.TAU

Math.abs(-5)
Math.sin(x)
Math.cos(x)
Math.tan(x)
Math.sqrt(16)
Math.pow(2, 8)
Math.log(x)
Math.log10(x)
Math.exp(x)
Math.floor(3.7)
Math.ceil(3.2)
Math.round(3.5)
Math.max(10, 20, 5)
Math.min(10, 20, 5)
Math.random()
Math.randint(1, 100)
```

### Time Module
```haiku
let now = Time.now()
Time.sleep(1000)  // milliseconds
Time.format(now, "%Y-%m-%d %H:%M:%S")
```

### JSON Module
```haiku
let data = {"name": "Haiku", "version": 1.0}
let jsonStr = JSON.stringify(data)
let parsed = JSON.parse(jsonStr)
```

### File Module (In-Memory)
```haiku
File.write("hello.txt", "Hello!")
let content = File.read("hello.txt")
File.append("hello.txt", "\nMore text.")
println(File.exists("hello.txt"))
File.delete("hello.txt")
```

### Assertions
```haiku
assert(2 + 2 == 4, "Math still works")
```

---

## Error Handling

### try / catch / finally
```haiku
try {
    let x = 10
    let y = 0
    if y == 0 {
        throw "Cannot divide by zero!"
    }
    println(f"Result: {x / y}")
} catch e {
    println(f"Caught error: {e}")
} finally {
    println("Cleanup complete")
}
```

### throw
Use `throw` to raise an error from anywhere:
```haiku
fn divide(a, b) {
    if b == 0 {
        throw "Division by zero"
    }
    return a / b
}
```

### Error Tracebacks
When an unhandled error occurs, Haiku prints a full **call-stack traceback** with the exact line number where the error happened and every function call that led to it.

Example program (`bad_math.hku`):
```haiku
fn divide(a, b) {
    return a / b        // line 2 — error happens here
}

fn calc(x) {
    return divide(x, 0) // line 6
}

fn main() {
    let v = calc(10)    // line 10
}

main()                  // line 13
```

Output:
```
Traceback (most recent call last):
  at line 13 in fn 'main'
  at line 10 in fn 'calc'
  at line 6 in fn 'divide'
RuntimeError at line 2: Division by zero
```

The traceback reads **bottom-up** — the last line is where the error actually occurred, and the frames above it show the call chain that got there.

### Catching the error message
The `catch` variable receives the error message string:
```haiku
try {
    let result = 1 / 0
} catch err {
    println(f"Handled: {err}")   // Handled: Division by zero
}
```

### Unclosed Block Comments
If a `/* ... */` block comment is never closed, Haiku raises a clear error instead of silently swallowing the rest of the file:
```haiku
/* this comment is never closed
println("this line is NOT skipped — you get an error instead")
```
```
LexerError: Unterminated block comment starting at line 1
```

---

## Running Haiku

### Run a File
```bash
python main.py script.hku
# or
python -m haiku script.hku
```

### Interactive REPL
```bash
python main.py
# or
python -m haiku
```

### Run Inline Code
```bash
python main.py -c "println(42)"
# or
python -m haiku -c "println(42)"
```

### Package Mode (`python -m haiku`)
Because the `haiku/` directory contains a `__main__.py`, the entire package can be invoked directly with `-m`. This is handy when Haiku is installed as a library or when `main.py` is not in your working directory.

```bash
# From any directory where haiku/ is importable:
python -m haiku script.hku
python -m haiku --version
python -m haiku --help
```

### From Python
```python
from haiku import run

result = run('''
let x = 10
let y = 20
println(x + y)
''')

print(result.output)   # 30
if result.error:
    print(result.error)  # formatted traceback if something went wrong
```

---

## Project Structure

```
Haiku-main/
├── main.py               # Root entry point  →  python main.py
├── icon.ico
├── README.md
├── examples/
│   ├── hello.hku
│   ├── variables.hku
│   ├── functions.hku
│   ├── collections.hku
│   ├── control_flow.hku
│   ├── classes.hku
│   ├── math.hku
│   ├── json_file.hku
│   └── advanced.hku
└── haiku/                # The language package
    ├── __init__.py       # Public API + run() helper
    ├── __main__.py       # Package entry point  →  python -m haiku
    ├── cli.py            # CLI logic (shared by main.py & __main__.py)
    ├── lexer.py          # Tokenizer
    ├── parser.py         # Recursive-descent parser
    ├── ast_nodes.py      # AST node definitions (all nodes carry line numbers)
    ├── interpreter.py    # Tree-walking interpreter + traceback engine
    ├── values.py         # Runtime value types
    └── stdlib.py         # Built-in functions and modules
```

---

## Complete Example Programs

### Example 1: FizzBuzz
```haiku
for i in range(1, 21) {
    if i % 3 == 0 && i % 5 == 0 {
        println("FizzBuzz")
    } elif i % 3 == 0 {
        println("Fizz")
    } elif i % 5 == 0 {
        println("Buzz")
    } else {
        println(i)
    }
}
```

### Example 2: Fibonacci Sequence
```haiku
fn fibonacci(n) {
    if n <= 1 {
        return n
    }
    return fibonacci(n - 1) + fibonacci(n - 2)
}

for i in range(0, 10) {
    println(f"fib({i}) = {fibonacci(i)}")
}
```

### Example 3: Working with Data
```haiku
let users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]

let adults = users.filter((u) => u["age"] >= 30)
println(f"Adults: {adults}")

let names = users.map((u) => u["name"])
println(f"Names: {names}")

let totalAge = users.reduce((acc, u) => acc + u["age"], 0)
println(f"Average age: {totalAge / users.len()}")
```

---

## Language Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| F-Strings | Complete | Easy string interpolation with f"text {expr}" |
| R-Strings | Complete | Raw strings for regex/paths with r"text" |
| Module Imports | Complete | Import .hku files and built-in modules |
| Lexical Analysis | Complete | Keywords, identifiers, literals, comments, operators |
| Primitive Types | Complete | Number, String, Boolean, None |
| Collections | Complete | List, Map with rich native methods |
| Variables | Complete | let (mutable), const (immutable), block scope |
| Operators | Complete | Arithmetic, comparison, logical, bitwise, assignment, ternary |
| Control Flow | Complete | if/elif/else, for, while, match, break, continue |
| Functions | Complete | Named, anonymous, lambda, default params, variadic, closures, higher-order |
| OOP | Complete | Classes, inheritance, super, static methods, encapsulation |
| Error Handling | Complete | try/catch/finally, throw |
| Error Tracebacks | Complete | Full call-stack with exact line numbers on every runtime error |
| Unclosed Comment Detection | Complete | `/* */` that is never closed raises LexerError with line number |
| Package Mode | Complete | `python -m haiku` works alongside `python main.py` via `haiku/__main__.py` |
| Standard Library | Complete | I/O, Math, Time, JSON, File, type utilities |
| String Processing | Complete | Methods: upper, lower, trim, split, contains, replace, slice |
| List Processing | Complete | Methods: push, pop, shift, map, filter, reduce, sort, find |
| Map Processing | Complete | Methods: keys, values, entries, has, delete, clear |
| Assertions | Complete | assert(condition, message) |

---

## Packaging

### 1. Compile to Executable (`PyInstaller`)
To bundle the application into exe:
```powershell
pyinstaller --onefile --icon icon.ico --name haiku main.py
```

## License

Haiku is open source. Use it, modify it, and build amazing things with it!

---

**Happy Coding in Haiku!**
