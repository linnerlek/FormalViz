import sqlite3

class SQLite3():

  def __init__(self):
    self.relations = []
    self.attributes = {}
    self.domains = {}
    self.conn = None

  def open(self,dbfile):
    self.conn = sqlite3.connect(dbfile)
    query = "select name from sqlite_schema where type='table'"
    c = self.conn.cursor()
    c.execute(query)
    records = c.fetchall()
    for record in records:
      self.relations.append(record[0].upper())
    for rname in self.relations:
      query = "select name,type from pragma_table_info('"+rname+"')"
      c.execute(query)
      records = c.fetchall()
      attrs = []
      doms = []
      for record in records:
        attrs.append(record[0].upper())
        if record[1].upper().startswith("INT") or record[1].upper().startswith("NUM"):
          doms.append("INTEGER")
        elif record[1].upper().startswith("DEC"):
          doms.append("DECIMAL")
        else:
          doms.append("VARCHAR")
      self.attributes[rname] = attrs
      self.domains[rname] = doms

  def close(self):
    self.conn.close()

  def relationExists(self, rname):
    return rname.upper() in self.relations

  def getAttributes(self, rname):
    return self.attributes[rname.upper()]

  def getDomains(self, rname):
    return self.domains[rname.upper()]

  def displayDatabaseSchema(self):
    print("*********************************************")
    for rname in self.relations:
      print(rname+"(",end="")
      attrs = self.attributes[rname]
      doms = self.domains[rname]
      for i,(aname,atype) in enumerate(zip(attrs,doms)):
        if i == len(attrs)-1:
          print(aname+":"+atype+")")
        else:
          print(aname+":"+atype+",",end="")
    print("*********************************************")

  def displayQueryResults(self,query,tree):
    print("\nANSWER(",end="")
    nCols = len(tree.get_attributes())
    for i,col in enumerate(tree.get_attributes()):
      if i == (nCols-1):
        print(col+":"+tree.get_domains()[i]+")")
      else:
        print(col+":"+tree.get_domains()[i]+",",end="")
    # execute the query against sqlite3 database
    c = self.conn.cursor()
    #print("Executing query:",query)
    c.execute(query)
    records = c.fetchall()
    rowCount = len(records)
    print("Number of tuples = "+str(rowCount)+"\n")
    for record in records:
      for val in record:
        print(str(val)+":",end="")
      print()
    print()
    c.close()

  def isQueryResultEmpty(self,query):
    c = self.conn.cursor()
    records = c.execute(query)
    c.close()
    return len(records) == 0