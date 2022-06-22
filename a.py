# a='["a","b","c","d"]'
# print(a)
# print(type(a))

a=1
print(a[1])



import json

# # b=json.dumps(a)
# # print(b)
# # print(type(b))

# c=json.loads(a)

# print(c)
# print(type(c))


# from django.contrib.gis.geos import Point
# p1 = Point(37.2676483,-6.9273579)
# p2 = Point(37.2653293,-6.9249401)
# distance = p1.distance(p2)
# distance_in_km = distance * 100


a=['a','b']     #python object(list)
print(type(a))
print(a)

d=json.dumps(a)    # convert python to json(str)
print(d)
print(type(d))

c=json.loads(d)    #agian json to python(list)
print(c)
print(type(c))

print("__________")

x='["a","b"]'      #json object (str)
print(type(x))
print(x)

# d=json.dumps(a)    
# print(d)
# print(type(d))

y=json.loads(x)    #convert json to python
print(y)
print(type(y))


