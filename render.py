import pygame, random

# Initialise pygame
pygame.init()
screen = pygame.display.set_mode((800,800), vsync=True)
clock = pygame.time.Clock()
font = pygame.font.Font("freesansbold.ttf", 30)

# This is what the user is allowed to type in
allowed = "abc&|!()"

# Total set (8 is the only number not present in the subsets)
total = [1, 2, 3, 4, 5, 6, 7, 8]
sets = {
    "a":[1, 2, 3, 5],
    "b":[2, 3, 4, 8],
    "c":[3, 4, 5, 6]
}

# The sets were carefully chosen to ensure each set has 2 numbers corresponding toeach of the other sets, 1 number corresponding
#   to all three sets, and 1 number that is unique to that set. There is also 1 number (8) that is not in any sets.
# This way, sections can be shader based on whether or not that number is present. Additionally, new sets are created later on as
#   part of the order of operations parsing.

classifications = {
    1:"a",
    2:"ab",
    3:"abc",
    4:"bc",
    5:"ac",
    6:"c",
    7:"none",
    8:"b"
}

# Load the empty asset so that screen isn't blank on startup.
assets = {"empty":pygame.transform.scale(pygame.image.load("empty.png").convert_alpha(), [400, 400])}

# All other assets (1 for each shaded section)
for i in classifications.keys():
    # Load, scale, and convert each image.
    image = classifications[i]
    assets[image] = pygame.transform.scale(pygame.image.load(str(image) + ".png").convert_alpha(), [400, 400])

# This is for splitting a&b into a & b so they can be split by " "
def delim(expression):
    expression = " & ".join(expression.split("&"))
    expression = " | ".join(expression.split("|"))
    return expression

# Class so that they can be sorted by size (smaller ones always have a greater priority) w/o losing data related to start, end, size, and expression
class Span:
    def __init__(self, span, expression):
        self.start = span[0]
        self.end = span[1]
        self.size = self.end - self.start

        # Cut out the relevant part from the expression such that
        # a & (b & !c) -> b & !c
        self.expression = expression[self.start + 1:self.end]

# Sort custom span objects by size in ascending order for priorities
# A smaller span ALWAYS is a higher priority.
def sort_by_size(objects):
    # Apparently you can put a function in a function
    def sort_key(obj):
        return obj.size
    sorted_objects = sorted(objects, key=sort_key)
    return sorted_objects

# Enumerate through the expression and record
#   The start and finishing index of parentheses
#   in a custom Span object, sort by priority (size)
#   and then return.
def find_parentheses_spans(expression):
    stack = []
    spans = []
    for index, char in enumerate(expression):
        # When a starting bracket is found, record the next closing bracket that is found
        #   and associate them. If another opening is found this is disregarded.
        if char == '(':
            stack.append(index)
        elif char == ')':
            start = stack.pop()
            spans.append([start, index])
    # Orders them
    spans.sort(key=lambda x: x[0])
    # Puts into data class for sorting
    objects = [Span(span, expression) for span in spans]
    return sort_by_size(objects)

# Union of two sets (uses built in set type to disregard duplicates)
def union(set_1, set_2):
    result = set(set_1 + set_2)
    return list(result)

# Intersection of two sets (iterative approach)
def intersection(set_1, set_2):
    result = []
    for item in set_1:
        if item in set_2:
            # If the item is in both set_1 and set_2 then add it.
            result.append(item)
    return result

# Inverse of a set based on a total.
def complement(set_1, total):
    result = []
    for item in total:
        if item not in set_1:
            # If the item is in the total but not the set, add it.
            result.append(item)
    return result

# [Deprecated] but this used to turn "[1, 2, 3]" into [1, 2, 3] instead of ["[", "1", ... "]"] 
def string_to_list(string):
    string = string[1:len(string)-1]
    return string.split(", ")

# Remove the character at a specified index (for user input so that they can backspace at a certain index)
def remove_character_at_index(string, index):
    first_half = string[:index]
    second_half = string[index + 1:]
    return first_half + second_half

# Add a character at index (for user input so they can type anywhere in their input)
def insert_to_string(string, index, char):
    first_half = string[:index]
    second_half = string[index:]
    return first_half + char + second_half

# This parses an expression based on letters representing sets [including ones added later for layers of parentheses].
def parse(expression, sets, total, classifications):
    expression = delim(expression)
    # First split the expression down into the terms
    terms = expression.split(" ")
    operators = []  
    arrays = []
    # Replace A, B, C, ECT. with their corresponding arrays, inverse if necessary.
    for index, term in enumerate(terms):
        # [DEPRECATED] - this used to allow pre-calculated arrays (higher priority based on brackets)
        #   to be put in, but they are now represented by a new letter.
        if "[" in term:
            arrays.append(string_to_list(term))
        else:
            # Do not change operators but record indices.
            if term == "&" or term == "|":
                arrays.append(term)
                operators.append(index)
            is_not = "!" in term
            term = term.strip("!")
            # If the term contains a '!' character, instead append the complement of that set.
            if term in sets.keys():
                if is_not:
                    arrays.append(complement(sets[term], total))
                else:
                    # Else, just get the set corresponding to that term.
                    arrays.append(sets[term])

    # The result is [[1, 2, 3], "&", [3, 4, 5]] for example.
    for operator in operators:
        # We know that for each operator, there is a set on either side.
        set_1 = arrays[operator - 1]
        logic = arrays[operator]
        set_2 = arrays[operator + 1]
        # Combine the sets in either way.
        if logic == "&":
            result = intersection(set_1, set_2)
        elif logic == "|":
            result = union(set_1, set_2)
        # Remove the old sets & operator, add the combined set.
        for i in range(3): arrays.pop(operator - 1)
        arrays.insert(operator - 1, result)
        # Account for the size of the array shrinking.
        for index in range(len(operators)):
            operators[index] -= 2
    
    # Parsing done, clean up array.
    arrays = arrays[0]

    # Return final array
    return arrays

# Initalise expression string for user to type into
expression = ""

# This is the wrapper function for the parentheses and expression parsing functions.
def solve(expression):
    # Calculate the span priority of the expression.
    spans = find_parentheses_spans(expression)

    # Define the alphabet / used letters so that inner terms can be represented by a letter.
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    used = "abc"

    # Any new letters are added here (with the array they correspond to.)
    # Whilst evaluating a|(b&c), b&c would be done first and then added here under the
    #   alias of "d", then all subsequent uses of (b&c) are replaced by d.
    solved = {}

    # Iterate over each span (term contained within parentheses) and evaluate.
    for index, span in enumerate(spans):
        exp = span.expression.replace("(", "")
        exp = exp.replace(")", "")
        # Look to see if any terms have been solved previously (see above example with b&c).
        for key in solved.keys():
            if key in exp:
                # If we find one, replace it with its letter alias.
                exp = exp.replace(key, str(solved[key]))
        # Parse the new expression, so from the example:
        #   The first iteration would return b&c and save that to d as [3, 4]
        #   The second iteration would evaluate a|d and return [1, 2, 3, 4, 5]
        evaluated = parse(exp, sets, total, classifications)
        # Assign a new letter to THIS layer so that it can be used next.
        new_letter = alphabet[len(used)]
        used += new_letter
        sets[new_letter] = evaluated
        # Save it as a solved term.
        solved[exp] = new_letter
        # Continue repeating recursively until all terms have been evaluated.
    # Then return the last term (containing all other terms).
    return sets[used[-1]]

# Ready for looping
running = True
# Users cursor position (recall the insert_at_index functions earlier)
editing_index = 0

# List of different sections for use in puzzle creation
classification_list = ["a", "b", "c", "ab", "ac", "bc", "abc", "none"]

# Make a puzzle by choosing a random section.
def create_puzzle():
    sections = []
    length = random.randint(0, len(classification_list))
    for i in range(length):
        key = random.choice(classification_list)
        sections.append(key)
    # Ensure no duplicates for rendering efficiency.
    return list(set(sections))

# Prevent user from accidentally hitting keys and incrementing the cursor index. (Pygame event unicode bug.)
allowed_keys = [pygame.K_a, pygame.K_b, pygame.K_c]
allowed_with_shift = [49, 55, 92, 57, 48]

# Create inital puzzle.
puzzle = create_puzzle()

while running:
    # Attempt to parse user input
    try: sections = [classifications[x] for x in solve("(%s)" % expression)]
    except: pass

    keys = pygame.key.get_pressed()

    # Handle typing / exiting
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.unicode in allowed and event.key in allowed_keys or (event.key in allowed_with_shift and keys[1073742049]):
                editing_index += 1
                expression = insert_to_string(expression, editing_index, event.unicode)
            if event.key == pygame.K_BACKSPACE:
                expression = remove_character_at_index(expression, editing_index)
                editing_index -= 1
            if event.key == pygame.K_LEFT:
                editing_index -= 1
            if event.key == pygame.K_RIGHT:
                editing_index += 1
            if editing_index < 0: editing_index = 0
            if editing_index > len(expression) - 1 and len(expression) > 0:
                editing_index = len(expression) - 1

    # Refresh screen
    screen.fill((255, 255, 255))
    # Render

    # Render the users input & circles.
    text = font.render("(%s)" % expression, True, (0, 0, 0))
    screen.blit(text, (10, 750))
    
    text = font.render(str(editing_index), True, (0, 0, 0))
    screen.blit(text, (10, 700))

    #pygame.draw.line(screen, (255,0,0), [30 + editing_index * 10, 750], [30 + editing_index * 11, 780], 5)

    screen.blit(assets["empty"], (0,0))

    # Attempt to shade sections.
    try:
        for section in sections:
            if expression != "": screen.blit(assets[section], [0,0])
    except: pass

    # Draw the target puzzle
    for section in puzzle:
        screen.blit(assets[section], [400,0])

    # Check if the user is done.
    try:
        finished = True
        for item in puzzle:
            if item not in sections:
                finished = False
        if finished and len(puzzle) == len(sections):
            expression = ""
            puzzle = create_puzzle()
    except:
        pass

    # Update screen
    pygame.display.update()

# Free pygame memory
pygame.quit()   