# Haiku Programming Language

**Haiku** is a modern, expressive, general-purpose programming language inspired by Python. It is designed to be simple to learn yet powerful enough for real-world tasks. Haiku features a clean syntax, first-class functions, object-oriented programming, pattern matching, and a rich standard library.

- **File Extension**: `.hku`
- **Base Language**: Python (interpreter written in Python)
- **Paradigm**: Multi-paradigm (procedural, object-oriented, functional)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Language Syntax](#language-syntax)
3. [Data Types](#data-types)
4. [Variables & Constants](#variables--constants)
5. [Operators](#operators)
6. [Control Flow](#control-flow)
7. [Functions](#functions)
8. [Object-Oriented Programming](#object-oriented-programming)
9. [Collections](#collections)
10. [Standard Library](#standard-library)
11. [Error Handling](#error-handling)
12. [Running Haiku](#running-haiku)
13. [Project Structure](#project-structure)
14. [Complete Example Programs](#complete-example-programs)

---

## Quick Start

```haiku
// Hello World in Haiku
println("Hello, World!")

let name = "Haiku"
let version = 1.0

println("Language: " + name)
println("Version: " + version)
```

Run it:
```bash
python -m python_haiku hello.hku
```

Or use the interactive REPL:
```bash
python -m python_haiku
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
println("5! = " + fact)
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
    return "Hello, " + name + "!"
}

println(greet("Haiku"))
```

### Default Parameters
```haiku
fn greetWithTitle(name, title = "Mr./Ms.") {
    return "Hello, " + title + " " + name
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
        return this.name + " makes a sound"
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
        return this.name + " barks!"
    }

    fn info() {
        return super.info() + " (" + this.breed + ")"
    }
}

let dog = Dog("Buddy", "Golden Retriever")
println(dog.speak())
println(dog.info())
println(dog.breed)
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

println("Length: " + nums.len())
```

### Map Operations
```haiku
let scores = {"alice": 95, "bob": 87}

println(scores["alice"])
println("Keys: " + scores.keys())
println("Values: " + scores.values())
println("Entries: " + scores.entries())
println("Has 'alice': " + scores.has("alice"))

scores.delete("bob")
scores.clear()
println("Length: " + scores.len())
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
println("Hello, " + name)
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

```haiku
try {
    let x = 10
    let y = 0
    if y == 0 {
        throw("Cannot divide by zero!")
    }
    println("Result: " + (x / y))
} catch e {
    println("Caught error: " + e)
} finally {
    println("Cleanup complete")
}
```

---

## Running Haiku

### Run a File
```bash
python -m python_haiku script.hku
```

### Interactive REPL
```bash
python -m python_haiku
```

### Run Inline Code
```bash
python -m python_haiku -c "println(42)"
```

### From Python
```python
from python_haiku import run

result = run('''
let x = 10
let y = 20
println(x + y)
''')

print(result.output)
if result.error:
    print("Error:", result.error)
```

---

## Project Structure

```
python_haiku/
├── __init__.py       # Package entry point, run() helper
├── main.py           # CLI with REPL and file execution
├── lexer.py          # Tokenizer
├── parser.py         # Recursive-descent parser
├── ast_nodes.py      # AST node definitions
├── interpreter.py    # Tree-walking interpreter
├── values.py         # Runtime value types
├── stdlib.py         # Built-in functions and modules
├── README.md         # This documentation
└── examples/
    ├── hello.hku
    ├── variables.hku
    ├── functions.hku
    ├── collections.hku
    ├── control_flow.hku
    ├── classes.hku
    ├── math.hku
    ├── json_file.hku
    └── advanced.hku
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
    println("fib(" + i + ") = " + fibonacci(i))
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
println("Adults: " + adults)

let names = users.map((u) => u["name"])
println("Names: " + names)

let totalAge = users.reduce((acc, u) => acc + u["age"], 0)
println("Average age: " + (totalAge / users.len()))
```

---

## Language Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Lexical Analysis | Complete | Keywords, identifiers, literals, comments, operators |
| Primitive Types | Complete | Number, String, Boolean, None |
| Collections | Complete | List, Map with rich native methods |
| Variables | Complete | let (mutable), const (immutable), block scope |
| Operators | Complete | Arithmetic, comparison, logical, bitwise, assignment, ternary |
| Control Flow | Complete | if/elif/else, for, while, match, break, continue |
| Functions | Complete | Named, anonymous, lambda, default params, variadic, closures, higher-order |
| OOP | Complete | Classes, inheritance, super, static methods, encapsulation |
| Error Handling | Complete | try/catch/finally, throw |
| Standard Library | Complete | I/O, Math, Time, JSON, File, type utilities |
| String Processing | Complete | Methods: upper, lower, trim, split, contains, replace, slice |
| List Processing | Complete | Methods: push, pop, shift, map, filter, reduce, sort, find |
| Map Processing | Complete | Methods: keys, values, entries, has, delete, clear |
| Assertions | Complete | assert(condition, message) |

---

## License

Haiku is open source. Use it, modify it, and build amazing things with it!

---

**Happy Coding in Haiku!**
