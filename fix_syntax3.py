import sys

f = '/home/scott/Documents/FAA/nms-monitor/src/reporting/compare_services.py'
with open(f, 'r') as file:
    c = file.read()

c = c.replace('st.replace(\\"bold \\", \\"\\")', "st.replace('bold ', '')")
c = c.replace("style=\\'color:", "style='color:")
c = c.replace(";\\'>", ";'>")

with open(f, 'w') as file:
    file.write(c)

f2 = '/home/scott/Documents/FAA/nms-monitor/src/reporting/analyze_matrix.py'
with open(f2, 'r') as file:
    c2 = file.read()

c2 = c2.replace("style=\\'color:", "style='color:")
c2 = c2.replace(";\\'>", ";'>")

with open(f2, 'w') as file:
    file.write(c2)
