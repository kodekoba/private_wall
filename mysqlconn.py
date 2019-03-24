import pymysql.cursors      # a cursor is the object we use to interact with the database

class MySQLConnection:      # this class will give us an instance of a connection to our database
    def __init__(self,db):
        connection = pymysql.connect(host = 'localhost',
                                    user = 'root',  # change the user and pw as needed
                                    password = 'root',
                                    db = db,
                                    charset = 'utf8mb4',
                                    cursorclass = pymysql.cursors.DictCursor,
                                    autocommit = True)
        self.connection = connection    # establish the connection to the database
    
    def query_db(self, query, data=None):   # the method to query the database
        with self.connection.cursor() as cursor:
            try:
                query = cursor.mogrify(query, data)
                print("Running Query: ", query)

                executable = cursor.execute(query, data)
                if query.lower().find("insert") >= 0:
                    self.connection.commit()    # INSERT queries will return the ID NUMBER of the row inserted
                    return cursor.lastrowid
                elif query.lower().find("select") >= 0:
                    result = cursor.fetchall()  # SELECT queries will return the data from the database as a LIST OF DICTIONARIES
                    return result
                else:
                    self.connection.commit()    # UPDATE and DELETE queries will return nothing

            except Exception as e:
                print("something went wrong", e)    #if the query fails the method will return FALSE
                return False
            finally:
                self.connection.close()     # close the connection
# connectToMySQL receives the database we're using and uses it to create an instance of MySQLConnection
def connectToMySQL(db):
    return MySQLConnection(db)