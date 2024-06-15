import json,time

def db_insert(db_name,key,data):
    with open(db_name+".json","r+") as database:
        db_array = json.load(database)
        db_array[key].append(data)
        database.seek(0)
        json.dump(db_array, database,indent=1)
        database.close()

def db_read(db_name,key):
    with open(db_name+".json","r") as database:
        db_array = json.load(database)
        return db_array
        database.close()


def db_update_field(db_name,key,oid,field,value):
    with open(db_name+".json","r+") as database:
        db_array = json.load(database)
        for r in range(len(db_array[key])):
            if db_array[key][r]["CID"] == oid:
                db_array[key][r][field] = value
        database.seek(0)
        database.truncate()
        json.dump(db_array, database, indent=1)
        database.close()


def db_update(db_name,key,data):
    with open(db_name+".json","w") as database:
        db_array = {key:data}
        json.dump(db_array, database,indent=1)
        database.close()


def db_get_field(db_name,key,CID,field):
    with open(db_name+".json","r") as database:
        db_array = json.load(database)
        for r in range(len(db_array[key])):
            if db_array[key][r]["CID"] == CID:
                database.close()
                return str(db_array[key][r][field])
    print("field not found")
