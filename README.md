# code-grader

Generate a PDF of graded source files as a feedback for students

## Installation

- Please ensure that **latexmk** is in `$PATH`!
- We use the `minted` and the `geometry` LaTeX package
- Install this package

```bash
pip3 install -e .
```

## Usage

```bash
code-grader Signal.java LinearFilter.java
```

where `Signal.java` `LinearFilter.java` are Java source code files somewhere in the directory structure of current
directory.

More options:

```bash
code-grader -h
```

## Magic Comments

Comment your code with 

 - `/// <-` Hint for the students
 - `// [task blub: X/Y points]` Grading for a subtask
