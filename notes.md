our first logic starts from the build graph function

the purpose is to represent a list of tuples as an "dictionary" of relationships where they key is the name of a person and the object is a "set" to make sure the value are unique of their friends

for example we have 2 groups initial as our start value

precious and celine who are friends

then we have celine who is friends with goodness

so celeine is friends with precious and goodness hence two items in the set but preicous is just friends with celine

first thing first we initialise two variables, our graph and our name look up to track which names we've seen

next line is that we iterate for person a and b in our list of tuples

we create two variables, 'key_a' and 'key_b' which are safe versions/formatted versions of our person

we check our lookup dictionary to safe check that
if this person (key_a) is not in our dictionary

we make an item in the diction where key_a is the key and person_a is the value

we do the same for key_b

now we move on to prefilling the graph
