import sys

f = '/home/scott/Documents/FAA/nms-monitor/src/reporting/analyze_matrix.py'
with open(f, 'r') as file:
    c = file.read()

c = c.replace("s[\\'System\\']", 's["System"]')
c = c.replace("s[\\'Non-Standard IDs\\']", 's["Non-Standard IDs"]')
c = c.replace("s[\\'Unknown NOF Count\\']", 's["Unknown NOF Count"]')

with open(f, 'w') as file:
    file.write(c)
