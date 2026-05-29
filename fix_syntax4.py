import sys

f = '/home/scott/Documents/FAA/nms-monitor/src/reporting/compare_services.py'
with open(f, 'r') as file:
    c = file.read()

c = c.replace('b[\\"count\\"]', "b['count']")

with open(f, 'w') as file:
    file.write(c)
