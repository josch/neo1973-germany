x = 255
list = []
while x != 0:
    x2 = x%2
    list.append(x2)
    x = x/2
print list
for i in reversed(list):
    print i, 

