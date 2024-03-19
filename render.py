import pygame

pygame.init()
screen = pygame.display.set_mode((800,800), vsync=True)
clock = pygame.time.Clock()
font = pygame.font.Font("freesansbold.ttf", 30)
allowed = "abc&|!"

def union(set_1, set_2):
    result = set(set_1 + set_2)
    return list(result)

def intersection(set_1, set_2):
    result = []
    for item in set_1:
        if item in set_2:
            result.append(item)
    return result

def complement(set_1, total):
    result = []
    for item in total:
        if item not in set_1:
            result.append(item)
    return result

def parse(expression, sets, total, classifications):
    # First split the expression down into the terms
    terms = expression.split(" ")
    operators = []
    arrays = []
    # Replace A, B, C with their corresponding arrays, inverse if necessary.
    for index, term in enumerate(terms):
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
                arrays.append(sets[term])

    # [[1, 2, 3], "&", [3, 4, 5]] for example.
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
    sections = []
    arrays = arrays[0]

    # Figure out which sections must be rendered.
    for number in arrays:
        sections.append(classifications[number])
    return sections


total = [1, 2, 3, 4, 5, 6, 7, 8]
sets = {
    "a":[1, 2, 3, 5],
    "b":[2, 3, 4, 8],
    "c":[3, 4, 5, 6]
}

# The sets were carefully chosen to ensure each set has 2 numbers corresponding toeach of the other sets, 1 number corresponding
#   to all three sets, and 1 number that is unique to that set. There is also 1 number (8) that is not in any sets.
# This way, sections can be shader based on whether or not that number is present.
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
assets = {"empty":pygame.image.load("empty.png").convert_alpha()}

for i in classifications.keys():
    image = classifications[i]
    assets[image] = pygame.image.load(str(image) + ".png").convert_alpha()

# & -> intersection | -> union ! -> complement
expression = ""

running = True
while running:
    # Attempt to parse user input
    try: sections = parse(expression, sets, total, classifications)
    except: pass

    # Handle typing / exiting
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.unicode in allowed:
                expression += event.unicode
            if event.key == pygame.K_BACKSPACE:
                expression = expression[:len(expression)-1]
            if event.key == pygame.K_SPACE:
                expression += " "

    # Refresh screen
    screen.fill((255, 255, 255))
    # Render

    # Render the users input & circles.
    text = font.render(expression, True, (0, 0, 0))
    screen.blit(text, (10, 750))
    screen.blit(assets["empty"], (0,0))

    # Attempt to shade sections.
    try:
        for section in sections:
            screen.blit(assets[section], [0,0])
    except: pass

    pygame.display.update()

pygame.quit()