"""Idempotent Python Full Stack quiz curriculum seed."""
from app.extensions import db
from app.models.course import Course
from app.models.quiz import Quiz, QuizQuestion
from app.models.user import User


def _fact(concept, answer, wrong, code, output, code_wrong,
          practical=None, practical_answer=None, practical_wrong=None):
    if isinstance(wrong, str):
        wrong = [wrong, f"It always returns None for {concept}", f"It is unrelated to {concept}"]
    if isinstance(code_wrong, str):
        code_wrong = [code_wrong, 'The code raises an error', 'The code produces no value']
    practical = practical or f"Which choice correctly applies the rule for {concept}?"
    practical_answer = practical_answer or answer
    practical_wrong = practical_wrong or wrong
    return {
        'concept': concept,
        'answer': answer,
        'wrong': wrong,
        'code': code,
        'output': output,
        'code_wrong': code_wrong,
        'practical': practical,
        'practical_answer': practical_answer,
        'practical_wrong': practical_wrong,
    }


def _questions(facts):
    questions = []
    for index, fact in enumerate(facts):
        variants = [
            (
                f"Which statement is correct about {fact['concept']}?",
                fact['answer'], fact['wrong'],
                f"{fact['answer']} is the key idea behind {fact['concept']}."
            ),
            (
                f"What is the output of this Python code?\n{fact['code']}",
                fact['output'], fact['code_wrong'],
                f"The code produces {fact['output']}. This follows directly from the Python rule being tested."
            ),
            (
                fact['practical'],
                fact['practical_answer'], fact['practical_wrong'],
                f"{fact['practical_answer']} is correct because it applies the relevant Python rule safely and directly."
            ),
        ]
        for variant_index, (text, answer, wrong, explanation) in enumerate(variants):
            options = [answer] + list(wrong)
            rotation = (index * 3 + variant_index) % 4
            options = options[rotation:] + options[:rotation]
            correct = 'ABCD'[options.index(answer)]
            questions.append({
                'question_text': text,
                'options': options,
                'correct_option': correct,
                'explanation': explanation,
                'order_index': len(questions),
            })
    return questions


TOPICS = [
    ('Introduction to Python', [
        _fact('Python as an interpreted language', 'Python executes statements through its interpreter', ['Python only runs after C compilation', 'Python cannot run scripts', 'Python is only a markup language'], 'print("Hi")', 'Hi', ['"Hi"', 'None', 'SyntaxError'], 'Which command correctly runs a file named main.py?', 'python main.py', ['run main.py', 'execute python main.py', 'start main']),
        _fact('the print function', 'print() displays values', ['print() stores values permanently', 'print() creates a class', 'print() imports modules'], 'print(2 + 3)', '5', ['23', '2 3', 'Error'], 'How should you display the text Hello?', 'print("Hello")', ['display("Hello")', 'echo Hello', 'show("Hello")']),
        _fact('Python indentation', 'Indentation groups related statements', ['Indentation is ignored everywhere', 'Indentation names variables', 'Indentation converts strings'], 'if True:\n    print("yes")', 'yes', ['True', 'if yes', 'IndentationError'], 'Which block is correctly indented?', 'if score >= 50:\n    print("Pass")', ['if score >= 50: print("Pass") only', 'if score >= 50\n print("Pass")', 'if score >= 50 -> print("Pass")']),
        _fact('identifiers', 'An identifier can contain letters, digits, and underscores but cannot start with a digit', 'An identifier must contain a space', 'student_2 = "Asha"\nprint(student_2)', 'Asha', ['student 2', 'student-2', '2student'], 'Which is a valid variable name?', 'total_marks', ['total-marks', '2total', 'class']),
        _fact('string literals', 'Text inside matching quotes is a string', 'Quoted text is always a number', 'name = "Mina"\nprint(name)', 'Mina', ['"Mina" with quotes', 'MinaMina', 'NameError'], 'Which creates a string value?', 'language = "Python"', ['language = Python', 'language = 3.14', 'language = string(Python)']),
        _fact('integer values', 'An integer is a whole number without a decimal part', 'An integer must be quoted', 'value = 12\nprint(type(value).__name__)', 'int', ['str', 'float', 'number'], 'Which value is an integer?', '42', ['42.0', '"42"', 'True']),
        _fact('comments', 'A hash starts a single-line comment in Python', 'A hash always performs division', 'print("A")  # greeting', 'A', ['A greeting', '# greeting', 'Error'], 'How do you write a single-line comment?', '# explain this line', ['// explain this line', '<!-- explain this line -->', '/* explain this line */']),
        _fact('basic arithmetic', 'The plus operator adds numeric values', 'The plus operator always divides values', 'print(7 + 4)', '11', ['74', '3', '28'], 'Which expression adds two values?', 'first + second', ['first / second', 'first ** second only', 'add(first, second)']),
        _fact('case sensitivity', 'Python treats Name and name as different identifiers', 'Python ignores letter case', 'name = "A"\nName = "B"\nprint(name)', 'A', ['B', 'AB', 'NameError'], 'Which statement is true about variable names?', 'count and Count are different names', ['count and Count are identical', 'only uppercase names work', 'names may contain spaces']),
        _fact('the main script entry point', 'if __name__ == "__main__" runs code when the file is executed directly', 'It runs only when imported', 'if __name__ == "__main__":\n    print("run")', 'run', ['__main__', 'True only', 'Nothing always'], 'Which pattern protects code from running on import?', 'if __name__ == "__main__":', ['if main == true:', 'when __main__:', 'run_if_main()']),
    ]),
    ('Comments, Variables, Data Types & Type Testing', [
        _fact('variable assignment', 'The equals sign assigns the value on its right to the name on its left', 'The equals sign compares two values', 'x = 5\nx = x + 2\nprint(x)', '7', ['52', '5', 'NameError'], 'Which statement updates points by 10?', 'points = points + 10', ['points == points + 10', 'points += "10" only', 'update points 10']),
        _fact('multiple assignment', 'Multiple names can receive values in one assignment', 'Only one variable can be assigned per line', 'a, b = 1, 2\nprint(b)', '2', ['1', '1,2', 'Error'], 'Which assigns 3 to x and 4 to y?', 'x, y = 3, 4', ['x = 3, y = 4', 'x;y = 3;4', 'assign x,y 3,4']),
        _fact('the bool type', 'bool stores True or False', 'bool stores only text', 'print(type(False).__name__)', 'bool', ['boolean', 'str', 'FalseType'], 'Which is a Boolean value?', 'False', ['"False"', '0.0 only', 'false']),
        _fact('type()', 'type() reports the type of a value', 'type() converts every value to text', 'print(type(3.5).__name__)', 'float', ['int', 'decimal', 'str'], 'How do you inspect the type of value x?', 'type(x)', ['typeof x', 'x.type()', 'kind(x)']),
        _fact('type conversion', 'int("8") converts the numeric string to an integer', 'int() converts every string to a list', 'print(int("8") + 2)', '10', ['82', '8.2', 'TypeError'], 'Which converts user text to an integer?', 'int(text)', ['integer(text)', 'text.to_int only', 'convert int text']),
        _fact('float values', 'A float represents a number with a decimal component', 'A float must be a Boolean', 'price = 2.5\nprint(type(price).__name__)', 'float', ['int', 'decimalstr', 'number'], 'Which value has float type?', '6.25', ['"6.25"', '6', 'six']),
        _fact('None', 'None represents the absence of a value', 'None is the same as zero', 'result = None\nprint(result is None)', 'True', ['False', 'NoneType text', '0'], 'Which value means no result was produced?', 'None', ['0', '"None" only', 'False always']),
        _fact('augmented assignment', '+= adds to a variable and stores the new value', '+= compares values', 'total = 4\ntotal += 3\nprint(total)', '7', ['43', '3', 'SyntaxError'], 'Which is equivalent to count = count + 1?', 'count += 1', ['count ==+ 1', 'count =+ 1 only', 'count plus 1']),
        _fact('mutable versus immutable basics', 'Lists are mutable while strings are immutable', 'Both lists and strings are always immutable', 'items = [1]\nitems.append(2)\nprint(items)', '[1, 2]', ['[1]', '1,2', 'AttributeError'], 'Which value can be changed in place?', '[1, 2]', ['"[1, 2]"', '(1, 2)', 'None']),
        _fact('isinstance()', 'isinstance(value, type) checks whether a value has a type', 'isinstance() prints a value', 'print(isinstance(4, int))', 'True', ['int', '4', 'False'], 'Which checks whether x is a string?', 'isinstance(x, str)', ['type(x) == string', 'x.is_string()', 'is_string(x)']),
    ]),
    ('Control Statements & Looping Statements', [
        _fact('if statements', 'An if block runs when its condition is true', 'An if block always runs twice', 'if 3 > 1:\n    print("yes")', 'yes', ['3 > 1', 'True yes', 'Nothing'], 'Which condition checks that age is at least 18?', 'if age >= 18:', ['if age => 18:', 'if age >== 18:', 'if age equals 18:']),
        _fact('elif', 'elif tests another condition when earlier conditions were false', 'elif always runs before if', 'x = 2\nif x > 2: print("A")\nelif x == 2: print("B")', 'B', ['A', 'AB', 'Nothing'], 'Which keyword tests a second condition?', 'elif', ['else if only', 'elseif in all Python versions', 'nextif']),
        _fact('else', 'else runs when no preceding condition is true', 'else requires its own condition', 'if False:\n    print("A")\nelse:\n    print("B")', 'B', ['A', 'False', 'SyntaxError'], 'Which block handles the fallback case?', 'else:', ['otherwise:', 'default if:', 'fallback()']),
        _fact('for loops', 'A for loop visits each item in an iterable', 'A for loop runs only once', 'for n in [1, 2, 3]:\n    print(n, end=" ")', '1 2 3', ['123', '0 1 2', 'Error'], 'Which loop visits every name in names?', 'for name in names:', ['loop name names:', 'for names as name:', 'foreach name(names):']),
        _fact('range()', 'range(3) produces 0, 1, and 2', 'range(3) produces 1, 2, and 3', 'print(list(range(3)))', '[0, 1, 2]', ['[1, 2, 3]', '[0, 3]', 'range object only']),
        _fact('while loops', 'A while loop continues while its condition remains true', 'while loops never need a condition', 'n = 1\nwhile n < 3:\n    print(n, end=" ")\n    n += 1', '1 2', ['1 2 3', '2 3', 'Infinite 1'], 'What prevents a counting while loop from becoming infinite?', 'Update the loop variable', ['Remove the condition', 'Use print only', 'Use an unchanged variable']),
        _fact('break', 'break exits the nearest loop immediately', 'break skips only one expression', 'for n in range(4):\n    if n == 2: break\n    print(n, end=" ")', '0 1', ['0 1 2 3', '2 3', '1 2']),
        _fact('continue', 'continue skips the rest of the current iteration', 'continue exits the program', 'for n in range(3):\n    if n == 1: continue\n    print(n, end=" ")', '0 2', ['0 1 2', '1', '2']),
        _fact('nested loops', 'A nested loop runs the inner loop for each outer iteration', 'Nested loops run the inner loop only once', 'for a in [1, 2]:\n    for b in ["x", "y"]:\n        print(a, b)', '1 x 1 y 2 x 2 y', ['1 x 2 y', 'x y', '1 2']),
        _fact('conditional expressions', 'A conditional expression chooses one of two values', 'It defines a function', 'x = 5\nresult = "yes" if x > 3 else "no"\nprint(result)', 'yes', ['no', 'True', 'yesno'], 'Which expression assigns a positive label?', 'label = "positive" if n > 0 else "not positive"', ['if n > 0 then label', 'label = positive when n', 'choose(label, n > 0)']),
    ]),
    ('Lists', [
        _fact('list indexing', 'The first list index is zero', 'The first list index is one', 'items = ["a", "b"]\nprint(items[0])', 'a', ['b', '0', 'IndexError']),
        _fact('negative indexing', 'Index -1 selects the last list item', 'Negative indexes always fail', 'items = [10, 20, 30]\nprint(items[-1])', '30', ['10', '20', '-1']),
        _fact('list slicing', 'A slice excludes its stop index', 'A slice includes only the stop index', 'nums = [0, 1, 2, 3]\nprint(nums[1:3])', '[1, 2]', ['[1, 2, 3]', '[0, 1]', '[3]']),
        _fact('append()', 'append() adds one item at the end', 'append() removes the last item', 'x = [1]\nx.append(2)\nprint(x)', '[1, 2]', ['[2]', '[1]', 'None']),
        _fact('extend()', 'extend() adds each item from an iterable', 'extend() nests the whole iterable as one item', 'x = [1]\nx.extend([2, 3])\nprint(x)', '[1, 2, 3]', ['[1, [2, 3]]', '[2, 3, 1]', '[1]']),
        _fact('insert()', 'insert(index, value) places an item at a chosen position', 'insert() only works at the end', 'x = ["a", "c"]\nx.insert(1, "b")\nprint(x)', '["a", "b", "c"]', ['["b", "a", "c"]', '["a", "c", "b"]', 'None']),
        _fact('remove()', 'remove(value) deletes the first matching value', 'remove() deletes by index only', 'x = [1, 2, 2]\nx.remove(2)\nprint(x)', '[1, 2]', ['[1]', '[2, 2]', 'IndexError']),
        _fact('pop()', 'pop() removes and returns an item, defaulting to the last', 'pop() only reads an item', 'x = [1, 2]\nprint(x.pop())', '2', ['1', '[1]', 'None']),
        _fact('list comprehensions', 'A list comprehension builds a list from an iterable', 'A list comprehension creates a tuple only', 'print([n * 2 for n in [1, 2, 3]])', '[2, 4, 6]', ['[1, 2, 3]', '2,4,6', 'None']),
        _fact('sorting lists', 'sort() changes a list into ascending order by default', 'sort() always returns a new list', 'x = [3, 1, 2]\nx.sort()\nprint(x)', '[1, 2, 3]', ['[3, 1, 2]', 'None', '[2, 1, 3]']),
    ]),
    ('Strings', [
        _fact('string indexing', 'Strings support zero-based indexing', 'Strings can only be indexed from one', 'word = "Python"\nprint(word[1])', 'y', ['P', 't', '1']),
        _fact('string slicing', 'String slices return a substring and exclude the stop index', 'String slices reverse text automatically', 'print("Python"[0:2])', 'Py', ['Pyt', 'ython', 'on']),
        _fact('string concatenation', 'The plus operator joins strings', 'The plus operator sorts strings', 'print("Py" + "thon")', 'Python', ['Py thon', 'Py+thon', 'Error']),
        _fact('upper()', 'upper() returns a copy with letters in uppercase', 'upper() changes numbers to strings', 'print("py".upper())', 'PY', ['py', 'Py', 'UPPER']),
        _fact('lower()', 'lower() returns a copy with letters in lowercase', 'lower() removes spaces only', 'print("PY".lower())', 'py', ['PY', 'Py', 'lower']),
        _fact('strip()', 'strip() removes whitespace from both ends by default', 'strip() removes every character', 'print("  hi  ".strip())', 'hi', ['  hi  ', 'hi  ', '  hi']),
        _fact('split()', 'split() breaks a string into a list', 'split() joins a list', 'print("a,b".split(","))', '["a", "b"]', ['"a" "b"', '["a,b"]', 'a,b']),
        _fact('join()', 'join() combines strings using the separator', 'join() splits a string into characters', 'print("-".join(["a", "b"]))', 'a-b', ['ab', '[a-b]', 'a - b']),
        _fact('f-strings', 'An f-string evaluates expressions inside braces', 'An f-string treats braces as comments', 'name = "Sam"\nprint(f"Hi {name}")', 'Hi Sam', ['Hi {name}', 'Hi name', 'Sam Hi']),
        _fact('find()', 'find() returns the first index of a substring or -1', 'find() always returns True', 'print("banana".find("na"))', '2', ['1', '3', 'True']),
    ]),
    ('Dictionaries & Tuples', [
        _fact('dictionary keys', 'Dictionary keys map to values and must be hashable', 'Dictionary keys must always be integers', 'user = {"name": "Asha"}\nprint(user["name"])', 'Asha', ['name', '"Asha"', 'KeyError']),
        _fact('dictionary get()', 'get() can read a missing key without raising KeyError', 'get() deletes a key', 'print({}.get("x", 0))', '0', ['None only', 'KeyError', 'x']),
        _fact('dictionary update', 'Assigning a known key replaces its value', 'Assigning a key always adds a duplicate', 'd = {"a": 1}\nd["a"] = 2\nprint(d["a"])', '2', ['1', '[1, 2]', 'KeyError']),
        _fact('dictionary items()', 'items() provides key-value pairs', 'items() returns only keys', 'd = {"a": 1}\nprint(list(d.items()))', '[("a", 1)]', ['["a"]', '[1]', '{("a", 1)}']),
        _fact('dictionary comprehension', 'A dictionary comprehension builds key-value pairs', 'It builds only a string', 'print({n: n * n for n in [1, 2]})', '{1: 1, 2: 4}', ['[1, 4]', '{1, 2}', '{n: n}']),
        _fact('tuple creation', 'A tuple is an ordered immutable collection', 'A tuple is always mutable', 'point = (2, 3)\nprint(point[0])', '2', ['3', '(2, 3)', 'TypeError']),
        _fact('one-item tuples', 'A comma is required to create a one-item tuple', 'Parentheses alone create a tuple', 'value = (5,)\nprint(type(value).__name__)', 'tuple', ['int', 'list', 'parentheses']),
        _fact('tuple unpacking', 'Tuple unpacking assigns its items to matching names', 'Unpacking combines all values into one string', 'a, b = (10, 20)\nprint(a + b)', '30', ['1020', '(10, 20)', 'Error']),
        _fact('in membership', 'in checks whether a key or item is present', 'in changes the dictionary', 'print("a" in {"a": 1})', 'True', ['1', 'False', 'KeyError']),
        _fact('dict versus tuple choice', 'A dictionary is useful for named lookup while a tuple suits fixed ordered data', 'Both structures require numeric indexes', 'record = ("Ada", 36)\nprint(record[0])', 'Ada', ['36', '(Ada, 36)', 'KeyError']),
    ]),
    ('Sets', [
        _fact('set uniqueness', 'A set stores each distinct value once', 'A set keeps every duplicate', 'print(sorted({1, 1, 2}))', '[1, 2]', ['[1, 1, 2]', '{1, 2}', '[2]']),
        _fact('set creation', 'set() creates an empty set', '{} creates an empty set', 'empty = set()\nprint(len(empty))', '0', ['1', 'None', '{}']),
        _fact('set add()', 'add() inserts one value into a set', 'add() inserts by position', 's = {1}\ns.add(2)\nprint(sorted(s))', '[1, 2]', ['[2]', '[1]', 'TypeError']),
        _fact('set remove()', 'remove() deletes a value and raises KeyError if absent', 'remove() silently accepts every missing value', 's = {1, 2}\ns.remove(1)\nprint(sorted(s))', '[2]', ['[1, 2]', '[1]', '[]']),
        _fact('set discard()', 'discard() deletes a value without raising if it is absent', 'discard() always raises KeyError', 's = {1}\ns.discard(9)\nprint(s)', '{1}', ['set()', '{9}', 'KeyError']),
        _fact('union', 'Union combines values from both sets', 'Union keeps only common values', 'print(sorted({1, 2} | {2, 3}))', '[1, 2, 3]', ['[2]', '[1, 3]', '[]']),
        _fact('intersection', 'Intersection keeps values present in both sets', 'Intersection keeps every value', 'print({1, 2} & {2, 3})', '{2}', ['{1, 2, 3}', '{1, 3}', 'set()']),
        _fact('difference', 'Difference keeps values in the left set but not the right', 'Difference always returns the right set', 'print({1, 2} - {2})', '{1}', ['{2}', '{1, 2}', 'set()']),
        _fact('subset testing', 'issubset() checks whether every value is contained in another set', 'issubset() compares insertion order', 'print({1, 2}.issubset({1, 2, 3}))', 'True', ['False', '{1, 2}', '3']),
        _fact('hashable set members', 'Set members must be hashable, so a tuple can be a member', 'Lists can always be set members', 's = {(1, 2)}\nprint(len(s))', '1', ['2', '0', 'TypeError']),
    ]),
    ('Functions & Advanced Functions', [
        _fact('defining functions', 'def creates a function', 'def immediately calls a function', 'def add(a, b):\n    return a + b\nprint(add(2, 3))', '5', ['add', '23', 'None']),
        _fact('return', 'return sends a value back to the caller', 'return only prints a value', 'def f():\n    return 4\nprint(f())', '4', ['None', 'f', 'return']),
        _fact('default arguments', 'A default argument is used when the caller omits that argument', 'Defaults must always be passed explicitly', 'def greet(name="Ada"): return name\nprint(greet())', 'Ada', ['name', 'None', 'Error']),
        _fact('keyword arguments', 'Keyword arguments identify parameters by name', 'Keyword arguments ignore parameter names', 'def area(w, h): return w * h\nprint(area(h=3, w=2))', '6', ['23', '2', 'TypeError']),
        _fact('*args', '*args collects extra positional arguments into a tuple', '*args collects keyword arguments into a dictionary', 'def total(*nums): return sum(nums)\nprint(total(1, 2, 3))', '6', ['123', '(1, 2, 3)', 'None']),
        _fact('**kwargs', '**kwargs collects extra keyword arguments into a dictionary', '**kwargs collects positional arguments', 'def show(**data): return data["x"]\nprint(show(x=7))', '7', ['x', '{x: 7}', 'None']),
        _fact('scope', 'A local variable is created inside a function scope', 'All local names are global automatically', 'x = 1\ndef f():\n    x = 2\n    return x\nprint(f(), x)', '2 1', ['1 2', '2 2', 'Error']),
        _fact('lambda functions', 'A lambda is a small anonymous function', 'A lambda can never return a value', 'double = lambda n: n * 2\nprint(double(4))', '8', ['6', '44', 'None']),
        _fact('recursion', 'A recursive function must have a base case', 'Recursion never needs a stopping condition', 'def count(n):\n    if n == 0: return 0\n    return 1 + count(n - 1)\nprint(count(2))', '2', ['1', '3', 'RecursionError']),
        _fact('first-class functions', 'Functions can be stored in variables and passed as arguments', 'Functions can only be called by their original name', 'def inc(x): return x + 1\nf = inc\nprint(f(2))', '3', ['2', 'inc', 'None']),
    ]),
    ('Mock Interview', [
        _fact('choosing a list or set', 'Use a set when fast membership and uniqueness are needed', 'Use a set when order and duplicates are essential', 'print(len(set([1, 1, 2, 3])))', '3', ['4', '2', '1']),
        _fact('truthiness', 'An empty list is falsey in a condition', 'An empty list is always truthy', 'if []: print("yes")\nelse: print("no")', 'no', ['yes', '[]', 'Error']),
        _fact('aliasing lists', 'Two names can refer to the same mutable list', 'Assignment always copies a list', 'a = [1]\nb = a\nb.append(2)\nprint(a)', '[1, 2]', ['[1]', '[2]', 'None']),
        _fact('copying lists', 'copy() creates a shallow copy of a list', 'copy() makes every nested object independent', 'a = [1, 2]\nb = a.copy()\nb.append(3)\nprint(a)', '[1, 2]', ['[1, 2, 3]', '[3]', 'Error']),
        _fact('enumerate()', 'enumerate() supplies an index and value while iterating', 'enumerate() sorts a list', 'for i, v in enumerate(["a"]): print(i, v)', '0 a', ['1 a', 'a 0', 'None']),
        _fact('zip()', 'zip() pairs items from iterables by position', 'zip() combines all values into one string', 'print(list(zip([1, 2], ["a", "b"])))', '[(1, "a"), (2, "b")]', ['[(1, 2, "a", "b")]', '[1, 2, "a", "b"]', 'None']),
        _fact('function side effects', 'A function that mutates a passed list changes the shared list', 'Function arguments are always immutable copies', 'def add(xs): xs.append(2)\na = [1]\nadd(a)\nprint(a)', '[1, 2]', ['[1]', '[2]', 'None']),
        _fact('exception-safe lookup', 'get() is useful when a dictionary key may be missing', 'Indexing is always safer for missing keys', 'settings = {}\nprint(settings.get("theme", "light"))', 'light', ['None', 'theme', 'KeyError']),
        _fact('short-circuit and', 'and stops when the left side is false', 'and always evaluates both sides', 'print(False and (1 / 0))', 'False', ['0', 'ZeroDivisionError', 'True']),
        _fact('short-circuit or', 'or returns the first truthy operand', 'or always returns a Boolean object', 'print("ready" or "waiting")', 'ready', ['waiting', 'True', 'False']),
    ]),
    ('File Handling & Error Handling', [
        _fact('open mode r', 'Mode r opens an existing file for reading', 'Mode r deletes a file', 'with open("data.txt", "r") as f:\n    text = f.read()', 'file contents are read', ['file is overwritten', 'file is deleted', 'SyntaxError'], 'Which mode reads a text file?', 'r', ['w', 'a only', 'x only']),
        _fact('open mode w', 'Mode w writes and truncates an existing file', 'Mode w only reads', 'with open("data.txt", "w") as f:\n    f.write("new")', 'the file contains new', ['the file is unchanged', 'the file is read', 'FileNotFoundError always']),
        _fact('open mode a', 'Mode a appends data at the end of a file', 'Mode a removes existing data', 'with open("log.txt", "a") as f:\n    f.write("ok")', 'ok is added at the end', ['ok replaces all text', 'nothing is written', 'file is read']),
        _fact('with open', 'with closes the file automatically after the block', 'with leaves every file open forever', 'with open("x.txt") as f:\n    data = f.read()\nprint(f.closed)', 'True', ['False', 'None', 'FileError']),
        _fact('read()', 'read() returns file content as one string', 'read() returns only the filename', 'from io import StringIO\nf = StringIO("abc")\nprint(f.read())', 'abc', ['a b c', 'StringIO', 'None']),
        _fact('readline()', 'readline() reads one line at a time', 'readline() reads every file forever', 'from io import StringIO\nf = StringIO("a\\nb")\nprint(f.readline().strip())', 'a', ['b', 'a\\nb', 'None']),
        _fact('ValueError', 'ValueError means a value has the right type but an unsuitable value', 'ValueError only means a missing file', 'try:\n    int("abc")\nexcept ValueError:\n    print("bad")', 'bad', ['abc', 'TypeError', 'Nothing']),
        _fact('FileNotFoundError', 'FileNotFoundError occurs when a requested file does not exist', 'It occurs only for invalid integers', 'try:\n    open("missing.txt")\nexcept FileNotFoundError:\n    print("missing")', 'missing', ['FileNotFoundError text only', 'None', 'SyntaxError']),
        _fact('finally', 'finally runs whether an exception occurs or not', 'finally runs only after success', 'try:\n    print("work")\nfinally:\n    print("done")', 'work done', ['done work', 'work only', 'Error']),
        _fact('raising exceptions', 'raise deliberately signals an exception', 'raise silently ignores errors', 'try:\n    raise ValueError("bad")\nexcept ValueError:\n    print("handled")', 'handled', ['bad only', 'ValueError', 'Nothing']),
    ]),
    ('OOPs Part 1', [
        _fact('classes', 'A class defines a blueprint for objects', 'A class is always an instance only', 'class Dog:\n    pass\nprint(Dog.__name__)', 'Dog', ['object', 'pass', 'None']),
        _fact('objects', 'An object is an instance created from a class', 'Objects cannot hold data', 'class User: pass\nu = User()\nprint(isinstance(u, User))', 'True', ['User', 'False', 'None']),
        _fact('__init__', '__init__ initializes a new instance', 'init is called only when an object is deleted', 'class A:\n    def __init__(self): self.x = 3\na = A()\nprint(a.x)', '3', ['None', 'x', 'AttributeError']),
        _fact('self', 'self refers to the current object instance', 'self refers to the class name only', 'class A:\n    def value(self): return 4\nprint(A().value())', '4', ['self', 'A', 'None']),
        _fact('instance attributes', 'Instance attributes can differ between objects', 'All instances must share every attribute', 'class A: pass\na, b = A(), A()\na.x = 1\nb.x = 2\nprint(a.x)', '1', ['2', 'None', 'AttributeError']),
        _fact('class attributes', 'A class attribute is shared as a default through instances', 'Class attributes cannot be read by instances', 'class A: kind = "x"\nprint(A().kind)', 'x', ['kind()', 'None', 'AttributeError']),
        _fact('instance methods', 'An instance method receives self automatically when called through an object', 'Methods never receive the object', 'class A:\n    def f(self): return 1\nprint(A().f())', '1', ['self', 'A', 'TypeError']),
        _fact('inheritance', 'A child class can inherit behavior from a parent class', 'Inheritance prevents reuse', 'class Child(Parent): pass', 'Child inherits Parent', ['Parent inherits Child', 'Child is unrelated', 'SyntaxError']),
        _fact('method overriding', 'A child can provide a method with the same name to replace parent behavior', 'A child cannot define methods', 'class C:\n    def speak(self): return "C"\nprint(C().speak())', 'C', ['speak', 'None', 'Parent']),
        _fact('encapsulation convention', 'A leading underscore communicates internal-use intent', 'A single underscore makes a value truly private', 'class Account:\n    def __init__(self): self._balance = 0\nprint(Account()._balance)', '0', ['AttributeError', '_balance', 'None']),
    ]),
    ('OOPs Part 2', [
        _fact('super()', 'super() accesses parent-class behavior', 'super() creates a new unrelated class', 'class A:\n    def f(self): return "A"\nclass B(A):\n    def f(self): return super().f() + "B"\nprint(B().f())', 'AB', ['A', 'B', 'BA']),
        _fact('method resolution order', 'MRO determines the order Python searches classes for a method', 'MRO is the order objects are created', 'class A: pass\nprint(A.__mro__[0].__name__)', 'A', ['object', 'mro', 'None']),
        _fact('multiple inheritance', 'A class may inherit from more than one parent', 'Python classes can have only one parent', 'class C(A, B): pass', 'C has A and B as parents', ['A has C', 'C has no parents', 'SyntaxError']),
        _fact('property', '@property lets a method be accessed like an attribute', 'property must always be called with parentheses', 'class A:\n    @property\n    def x(self): return 5\nprint(A().x)', '5', ['x', 'None', 'TypeError']),
        _fact('classmethod', 'A classmethod receives the class as cls', 'A classmethod receives no first argument', 'class A:\n    @classmethod\n    def name(cls): return cls.__name__\nprint(A.name())', 'A', ['cls', 'name', 'None']),
        _fact('staticmethod', 'A staticmethod does not receive self or cls automatically', 'A staticmethod always receives self', 'class Math:\n    @staticmethod\n    def add(a, b): return a + b\nprint(Math.add(2, 3))', '5', ['23', 'Math', 'TypeError']),
        _fact('dunder __str__', '__str__ controls the friendly string representation of an object', 'str always displays the memory address only', 'class A:\n    def __str__(self): return "A object"\nprint(str(A()))', 'A object', ['A', '<A>', 'None']),
        _fact('abstract behavior', 'An abstract base class can require subclasses to implement methods', 'Abstract methods are automatically concrete', 'from abc import ABC, abstractmethod\nclass Shape(ABC):\n    @abstractmethod\n    def area(self): pass', 'Shape declares an abstract method', ['Shape is an object instance', 'area is called', 'SyntaxError']),
        _fact('dataclasses', 'A dataclass can generate common methods for data-holding classes', 'A dataclass cannot store fields', 'from dataclasses import dataclass\n@dataclass\nclass Point: x: int; y: int', 'Point is a data class', ['Point is a tuple only', 'x is a method', 'SyntaxError']),
        _fact('composition', 'Composition builds an object using another object as a component', 'Composition always requires inheritance', 'class Engine: pass\nclass Car:\n    def __init__(self): self.engine = Engine()', 'Car contains an Engine', ['Engine inherits Car', 'Car is a string', 'None']),
    ]),
]


def seed_python_full_stack_quizzes():
    """Replace Python Full Stack quiz content without creating duplicates."""
    course = Course.query.filter_by(name='Python Full Stack').first()
    if not course:
        raise RuntimeError('Python Full Stack course does not exist.')
    mentor = User.query.filter_by(role='mentor_admin').first()

    for quiz in course.quizzes.all():
        db.session.delete(quiz)
    db.session.flush()

    for day_number, (topic, facts) in enumerate(TOPICS, start=1):
        quiz = Quiz(
            title=f'Quiz {day_number}',
            description=f'Day {day_number}: {topic}',
            course_id=course.id,
            day_number=day_number,
            time_limit_minutes=0,
            total_marks=30,
            status='published',
            created_by=mentor.id if mentor else None,
        )
        db.session.add(quiz)
        db.session.flush()
        for question in _questions(facts):
            db.session.add(QuizQuestion(
                quiz_id=quiz.id,
                question_text=question['question_text'],
                option_a=question['options'][0],
                option_b=question['options'][1],
                option_c=question['options'][2],
                option_d=question['options'][3],
                correct_option=question['correct_option'],
                explanation=question['explanation'],
                marks=1,
                order_index=question['order_index'],
            ))

    db.session.commit()
