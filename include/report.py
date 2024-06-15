import json2table
import json, ast
from pandas import DataFrame
orders = json.load(open("db_orders.json",'r'))["Orders"]

columns = ["time1", "pair"]
data = []
for o in range(len(orders)):
    order = orders[o]
    for c in range(2):
        data.append([order[columns[0]],order[columns[1]]])

df = DataFrame(data)
df.columns=columns
report = open("report.html","w")
report.write("<pre>")
report.write(str(df))
report.write("</pre>")
