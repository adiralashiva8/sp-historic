import os
import mysql.connector
import logging
import math
import time
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta

def sphistoric_parser(opts):

    if opts.ignoreresult == "True":
        print("Ignoring execution results...")
        return

    # Read output.xml file
    print("Capturing execution results, This may take few minutes...")

    # connect to database
    mydb = connect_to_mysql_db(opts.host, opts.username, opts.password, opts.projectname)
    rootdb = connect_to_mysql_db(opts.host, opts.username, opts.password, 'sphistoric')

    # insert test results info into db
    df = pd.read_csv(opts.output)
    table = pd.pivot_table(df, index=["table","app_version"],
     values=["browser_time", "client_response_time", "response_time", "sql_count", "sql_time"])
    
    for line in table.to_csv(header=False, index=True).split('\n'):
        if line:
            values = line.split(',')
            result_id = insert_into_execution_table(mydb, rootdb, str(values[1]), opts.projectname)
            break

    for line in table.to_csv(header=False, index=True).split('\n'):
        if line:
            values = line.split(',')
            insert_into_test_table(mydb, result_id, str(values[0]), float(values[2]), float(values[3]), float(values[4]), float(values[5]), float(values[6]))

    print("INFO: Writing execution results to dB")
    commit_and_close_db(mydb)

# other useful methods
def connect_to_mysql_db(host, user, pwd, db):
    try:
        mydb = mysql.connector.connect(
            host=host,
            user=user,
            passwd=pwd,
            database=db
        )
        return mydb
    except Exception as e:
        print(e)

def insert_into_execution_table(con, ocon, name, projectname):
    cursorObj = con.cursor()
    rootCursorObj = ocon.cursor()
    sql = "INSERT INTO TB_EXECUTION (Execution_Id, Execution_Date, Execution_Desc) VALUES (%s, now(), %s);"
    val = (0, name)
    cursorObj.execute(sql, val)
    con.commit()
    cursorObj.execute("SELECT Execution_Id FROM TB_EXECUTION ORDER BY Execution_Id DESC LIMIT 1;")
    rows = cursorObj.fetchone()
    cursorObj.execute("SELECT COUNT(*) FROM TB_EXECUTION;")
    execution_rows = cursorObj.fetchone()
    # update sphistoric.TB_PROJECT table
    rootCursorObj.execute("UPDATE TB_PROJECT SET Last_Updated = now(), Total_Executions = %s WHERE Project_Name='%s';" % (execution_rows[0], projectname))
    ocon.commit()
    return str(rows[0])

def insert_into_test_table(con, eid, table_name, browser_time, client_response_time, response_time, sql_count, sql_time):
    cursorObj = con.cursor()
    sql = "INSERT INTO TB_TEST (Test_Id, Execution_Id, Table_Name, Browser_Time, Client_Response_Time, Response_Time, Sql_Count, Sql_Time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    val = (0, eid, table_name, browser_time, client_response_time, response_time, sql_count, sql_time)
    cursorObj.execute(sql, val)
    # Skip commit to avoid load on db (commit once execution is done as part of close)
    # con.commit()

def commit_and_close_db(db):
    # cursorObj = db.cursor()
    db.commit()
    # cursorObj.close()
    # db.close()
