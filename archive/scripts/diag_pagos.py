import csv
total = 0
empty_op = 0
sn_op = 0

with open(r'f:\JAVIER PRIVADO\APP PHYTON\ADMINISTRACION\csv\Pagos.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total += 1
        op = row.get('OP')
        if not op or str(op).strip() == "":
            empty_op += 1
        elif "S/N" in str(op):
            sn_op += 1

print(f"Total rows in Pagos.csv: {total}")
print(f"Empty OP:              {empty_op}")
print(f"S/N in OP:             {sn_op}")
print(f"Total skippable:       {empty_op + sn_op}")
print(f"Theoretical syncable:  {total - (empty_op + sn_op)}")
