from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import config
from .args import parse_options

app = Flask (__name__,
            static_url_path='', 
            static_folder='templates',
            template_folder='templates')

mysql = MySQL(app)

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/redirect')
def redirect_url():
    return render_template('redirect.html')

@app.route('/home', methods=['GET'])
def home():
    cursor = mysql.connection.cursor()
    use_db(cursor, "sphistoric")
    cursor.execute("SELECT * FROM TB_PROJECT;")
    data = cursor.fetchall()
    return render_template('home.html', data=data)

@app.route('/<db>/deldbconf', methods=['GET'])
def delete_db_conf(db):
    return render_template('deldbconf.html', db_name = db)

@app.route('/<db>/delete', methods=['GET'])
def delete_db(db):
    cursor = mysql.connection.cursor()
    cursor.execute("DROP DATABASE %s;" % db)
    # use_db(cursor, "sphistoric")
    cursor.execute("DELETE FROM sphistoric.TB_PROJECT WHERE Project_Name='%s';" % db)
    mysql.connection.commit()
    return redirect(url_for('home'))

@app.route('/newdb', methods=['GET', 'POST'])
def add_db():
    if request.method == "POST":
        db_name = request.form['dbname']
        db_desc = request.form['dbdesc']
        db_image = request.form['dbimage']
        cursor = mysql.connection.cursor()

        try:
            # create new database for project
            cursor.execute("Create DATABASE %s;" % db_name)
            # update created database info in sphistoric.TB_PROJECT table
            cursor.execute("INSERT INTO sphistoric.TB_PROJECT ( Project_Id, Project_Name, Project_Desc, Project_Image, Created_Date, Last_Updated, Total_Executions) VALUES (0, '%s', '%s', '%s', NOW(), NOW(), 0);" % (db_name, db_desc, db_image))
            # create tables in created database
            use_db(cursor, db_name)
            cursor.execute("Create table TB_EXECUTION ( Execution_Id INT NOT NULL auto_increment primary key, Execution_Date DATETIME, Execution_Desc TEXT);")
            cursor.execute("Create table TB_TEST ( Test_Id INT NOT NULL auto_increment primary key, Execution_Id INT, Table_Name TEXT, Browser_Time FLOAT, Client_Response_Time FLOAT, Response_Time FLOAT, Sql_Count FLOAT, Sql_Time FLOAT);")
            mysql.connection.commit()
        except Exception as e:
            print(str(e))

        finally:
            return redirect(url_for('home'))
    else:
        return render_template('newdb.html')

@app.route('/<db>/ehistoric', methods=['GET'])
def ehistoric(db):
    cursor = mysql.connection.cursor()
    use_db(cursor, db)
    cursor.execute("SELECT * from TB_EXECUTION order by Execution_Id desc LIMIT 500;")
    data = cursor.fetchall()
    return render_template('ehistoric.html', data=data, db_name=db)

@app.route('/<db>/deleconf/<eid>', methods=['GET'])
def delete_eid_conf(db, eid):
    return render_template('deleconf.html', db_name = db, eid = eid)

@app.route('/<db>/edelete/<eid>', methods=['GET'])
def delete_eid(db, eid):
    cursor = mysql.connection.cursor()
    use_db(cursor, db)
    # remove execution from tables: execution, suite, test
    cursor.execute("DELETE FROM TB_EXECUTION WHERE Execution_Id='%s';" % eid)
    cursor.execute("DELETE FROM TB_TEST WHERE Execution_Id='%s';" % eid)
    # get no. of executions
    cursor.execute("SELECT COUNT(*) from TB_EXECUTION;")
    exe_data = cursor.fetchall()

    # update sphistoric project
    cursor.execute("UPDATE sphistoric.TB_PROJECT SET Total_Executions=%s, Last_Updated=now() WHERE Project_Name='%s';" % (int(exe_data[0][0]), db))
    # commit changes
    mysql.connection.commit()
    return redirect(url_for('ehistoric', db = db))

@app.route('/<db>/metrics/<eid>', methods=['GET'])
def metrics(db, eid):
    cursor = mysql.connection.cursor()
    use_db(cursor, db)
    # Get testcase results of execution id
    cursor.execute("SELECT * from TB_TEST WHERE Execution_Id=%s;" % eid)
    test_data = cursor.fetchall()
    # get suite results of execution id
    cursor.execute("SELECT * from TB_EXECUTION WHERE Execution_Id=%s;" % eid)
    exe_data = cursor.fetchall()
    return render_template('metrics.html', exe_data=exe_data, test_data=test_data)

@app.route('/<db>/cmetrics', methods=['GET'])
def cmetrics(db):
    cursor = mysql.connection.cursor()
    use_db(cursor, db)
    eid_one = request.args.get('eid_one')
    eid_two = request.args.get('eid_two')
    # Get testcase results of execution id
    cursor.execute("SELECT * from TB_TEST WHERE Execution_Id=%s;" % eid_one)
    test_data_1 = cursor.fetchall()
    cursor.execute("SELECT * from TB_TEST WHERE Execution_Id=%s;" % eid_two)
    test_data_2 = cursor.fetchall()
    # get suite results of execution id
    cursor.execute("SELECT * from TB_EXECUTION WHERE Execution_Id=%s;" % eid_one)
    exe_data_1 = cursor.fetchall()
    cursor.execute("SELECT * from TB_EXECUTION WHERE Execution_Id=%s;" % eid_two)
    exe_data_2 = cursor.fetchall()
    return render_template('cmetrics.html', exe_data_1=exe_data_1, exe_data_2=exe_data_2, test_data_1=test_data_1, test_data_2=test_data_2)

@app.route('/<db>/tmetrics', methods=['GET', 'POST'])
def tmetrics(db):
    cursor = mysql.connection.cursor()
    use_db(cursor, db)

    # Get last row execution ID
    cursor.execute("SELECT Execution_Id from TB_EXECUTION order by Execution_Id desc LIMIT 1;")
    data = cursor.fetchone()
    # Get testcase results of execution id (typically last executed)
    cursor.execute("SELECT * from TB_TEST WHERE Execution_Id=%s;" % data)
    data = cursor.fetchall()
    return render_template('tmetrics.html', data=data, db_name=db)

@app.route('/<db>/tmetrics/<eid>', methods=['GET', 'POST'])
def eid_tmetrics(db, eid):
    cursor = mysql.connection.cursor()
    use_db(cursor, db)

    # Get testcase results of execution id (typically last executed)
    cursor.execute("SELECT * from TB_TEST WHERE Execution_Id=%s;" % eid)
    data = cursor.fetchall()
    return render_template('eidtmetrics.html', data=data, db_name=db)

@app.route('/<db>/search', methods=['GET', 'POST'])
def search(db):
    if request.method == "POST":
        search = request.form['search']
        cursor = mysql.connection.cursor()
        use_db(cursor, db)
        try:
            if search:
                cursor.execute("SELECT * from TB_TEST WHERE Table_Name LIKE '%{name}%' OR Execution_Id LIKE '%{name}%' ORDER BY Execution_Id DESC LIMIT 500;".format(name=search))
                data = cursor.fetchall()
                return render_template('search.html', data=data, db_name=db, error_message="")
            else:
                return render_template('search.html', db_name=db, error_message="Search text should not be empty")
        except Exception as e:
            print(str(e))
            return render_template('search.html', db_name=db, error_message="Could not perform search. Avoid single quote in search or use escaping character")
    else:
        return render_template('search.html', db_name=db, error_message="")

@app.route('/<db>/compare', methods=['GET', 'POST'])
def compare(db):
    if request.method == "POST":
        eid_one = request.form['eid_one']
        eid_two = request.form['eid_two']
        cursor = mysql.connection.cursor()
        use_db(cursor, db)
        # fetch first eid tets results
        cursor.execute("SELECT Table_Name, Execution_Id, Client_Response_Time, Sql_Time from TB_TEST WHERE Execution_Id=%s;" % eid_one )
        first_data = cursor.fetchall()
        # fetch second eid test results
        cursor.execute("SELECT Table_Name, Execution_Id, Client_Response_Time, Sql_Time from TB_TEST WHERE Execution_Id=%s;" % eid_two )
        second_data = cursor.fetchall()
        if first_data and second_data:
            # combine both tuples
            data = first_data + second_data
            sorted_data = sort_tests(data)
            return render_template('compare.html', data=sorted_data, db_name=db, fb = first_data, sb = second_data, eid_one = eid_one, eid_two = eid_two, error_message="")
        else:
            return render_template('compare.html', db_name=db, error_message="EID not found, try with existing EID")    
    else:
        return render_template('compare.html', db_name=db, error_message="")

@app.route('/<db>/mcompare', methods=['GET', 'POST'])
def mcompare(db):
    if request.method == "POST":
        eid_one = request.form['eid_one']
        eid_two = request.form['eid_two']
        cursor = mysql.connection.cursor()
        use_db(cursor, db)
        # fetch first eid tets results
        cursor.execute("SELECT Table_Name, Execution_Id, Client_Response_Time, Sql_Time from TB_TEST WHERE Execution_Id=%s;" % eid_one )
        first_data = cursor.fetchall()
        # fetch second eid test results
        cursor.execute("SELECT Table_Name, Execution_Id, Client_Response_Time, Sql_Time from TB_TEST WHERE Execution_Id=%s;" % eid_two )
        second_data = cursor.fetchall()

        if first_data and second_data:
            # combine both tuples
            data = first_data + second_data
            sorted_data = sort_tests(data)
            return render_template('mcompare.html', data=sorted_data, db_name=db, fb = first_data, sb = second_data,
             eid_one = eid_one, eid_two = eid_two, error_message="", show_link=1)
        else:
            return render_template('mcompare.html', db_name=db, error_message="EID not found, try with existing EID", show_link=0)    
    else:
        return render_template('mcompare.html', db_name=db, error_message="", show_link=0)

@app.route('/<db>/query', methods=['GET', 'POST'])
def query(db):
    if request.method == "POST":
        query = request.form['query']
        cursor = mysql.connection.cursor()
        use_db(cursor, db)
        try:
            cursor.execute("{name}".format(name=query))
            data = cursor.fetchall()
            return render_template('query.html', data=data, db_name=db, error_message="")
        except Exception as e:
            print(str(e))
            return render_template('query.html', db_name=db, error_message=str(e))
    else:
        return render_template('query.html', db_name=db, error_message="")

@app.route('/<db>/dashboardRecent', methods=['GET'])
def dashboardRecent(db):
    cursor = mysql.connection.cursor()
    use_db(cursor, db)

    cursor.execute("SELECT COUNT(Execution_Id) from TB_EXECUTION;")
    results_data = cursor.fetchall()
    cursor.execute("SELECT COUNT(Test_Id) from TB_TEST;")
    test_results_data = cursor.fetchall()

    if results_data[0][0] > 0 and test_results_data[0][0] > 0:

        cursor.execute("SELECT Execution_Id from TB_EXECUTION order by Execution_Id desc LIMIT 2;")
        exe_info = cursor.fetchall()

        if len(exe_info) == 1:
            pass
        else:
            exe_info = (exe_info[0], exe_info[0])
        
        cursor.execute("SELECT * from TB_TEST WHERE Execution_Id=%s;" % exe_info[0])
        last_exe_data = cursor.fetchall()

        cursor.execute("SELECT Table_Name, Client_Response_Time from TB_TEST WHERE Execution_Id=%s order by Client_Response_Time desc LIMIT 5;" % exe_info[0])
        crt_data = cursor.fetchall()

        cursor.execute("SELECT Table_Name, Sql_Time from TB_TEST WHERE Execution_Id=%s order by Sql_Time desc LIMIT 5;" % exe_info[0])
        sqlt_data = cursor.fetchall()

        cursor.execute("SELECT COUNT(Table_Name) from TB_TEST WHERE Execution_Id=%s" % exe_info[0])
        tables_data = cursor.fetchall()

        cursor.execute("SELECT ROUND(SUM(Client_Response_Time),2) from TB_TEST WHERE Execution_Id=%s" % exe_info[0])
        scrt_data = cursor.fetchall()

        cursor.execute("SELECT ROUND(SUM(Sql_Time),2) from TB_TEST WHERE Execution_Id=%s" % exe_info[0])
        ssqlt_data = cursor.fetchall()

        cursor.execute("SELECT Execution_Desc from TB_EXECUTION WHERE Execution_Id=%s;" % exe_info[0])
        desc_data = cursor.fetchall()
        app_version_data=desc_data[0][0]

        return render_template('dashboardRecent.html', last_exe_data=last_exe_data, exe_info=exe_info, db_name=db,
         crt_data=crt_data, tables_data=tables_data, sqlt_data=sqlt_data, scrt_data=scrt_data, ssqlt_data=ssqlt_data, app_version_data=app_version_data)    
    else:
        return redirect(url_for('redirect_url'))


@app.route('/<db>/dashboardRecentTwo', methods=['GET', 'POST'])
def dashboardRecentTwo(db):
    cursor = mysql.connection.cursor()
    use_db(cursor, db)
    cursor.execute("SELECT COUNT(Execution_Id) from TB_EXECUTION;")
    results_data = cursor.fetchall()
    cursor.execute("SELECT COUNT(Test_Id) from TB_TEST;")
    test_results_data = cursor.fetchall()

    if results_data[0][0] > 0 and test_results_data[0][0] > 0:

        if request.method == "POST":
            eid_one = request.form['eid_one']
            eid_two = request.form['eid_two']
            # fetch first eid tets results
            cursor.execute("SELECT Table_Name, Execution_Id, Client_Response_Time, Sql_Time from TB_TEST WHERE Execution_Id=%s;" % eid_one )
            first_data = cursor.fetchall()
            # fetch second eid test results
            cursor.execute("SELECT Table_Name, Execution_Id, Client_Response_Time, Sql_Time from TB_TEST WHERE Execution_Id=%s;" % eid_two )
            second_data = cursor.fetchall()

            cursor.execute("SELECT Execution_Desc from TB_EXECUTION WHERE Execution_Id=%s;" % eid_one)
            desc_data = cursor.fetchall()
            one_app_version_data=desc_data[0][0]

            cursor.execute("SELECT Execution_Desc from TB_EXECUTION WHERE Execution_Id=%s;" % eid_two)
            desc_data = cursor.fetchall()
            two_app_version_data=desc_data[0][0]

            if first_data and second_data:
                # combine both tuples
                data = first_data + second_data
                sorted_data = sort_tests(data)
                # print(sorted_data)
                return render_template('dashboardRecentTwo.html', data=sorted_data, db_name=db, fb = first_data, sb = second_data,
                 eid_one = eid_one, eid_two = eid_two, one_app_version_data=one_app_version_data, two_app_version_data=two_app_version_data, error_message="")
            else:
                return render_template('dashboardRecentTwo.html', db_name=db, error_message="EID not found, try with existing EID")    
        else:
            cursor.execute("SELECT Execution_Id from TB_EXECUTION order by Execution_Id desc LIMIT 2;")
            exe_info = cursor.fetchall()

            if len(exe_info) >= 2:
                exe_info = (exe_info[0][0], exe_info[1][0])
            else:
                exe_info = (exe_info[0][0], exe_info[0][0])

            eid_one = exe_info[0]
            eid_two = exe_info[1]
            # fetch first eid tets results
            cursor.execute("SELECT Table_Name, Execution_Id, Client_Response_Time, Sql_Time from TB_TEST WHERE Execution_Id=%s;" % eid_one )
            first_data = cursor.fetchall()
            # fetch second eid test results
            cursor.execute("SELECT Table_Name, Execution_Id, Client_Response_Time, Sql_Time from TB_TEST WHERE Execution_Id=%s;" % eid_two )
            second_data = cursor.fetchall()

            cursor.execute("SELECT Execution_Desc from TB_EXECUTION WHERE Execution_Id=%s;" % eid_one)
            desc_data = cursor.fetchall()
            one_app_version_data=desc_data[0][0]

            cursor.execute("SELECT Execution_Desc from TB_EXECUTION WHERE Execution_Id=%s;" % eid_two)
            desc_data = cursor.fetchall()
            two_app_version_data=desc_data[0][0]

            if first_data and second_data:
                # combine both tuples
                data = first_data + second_data
                sorted_data = sort_tests(data)
                # print(sorted_data)
                return render_template('dashboardRecentTwo.html', data=sorted_data, db_name=db, fb = first_data, sb = second_data,
                 eid_one = eid_one, eid_two = eid_two, one_app_version_data=one_app_version_data, two_app_version_data=two_app_version_data, error_message="")
            else:
                return render_template('dashboardRecentTwo.html', db_name=db, error_message="EID not found, try with existing EID")

    else:
        return redirect(url_for('redirect_url'))

def use_db(cursor, db_name):
    cursor.execute("USE %s;" % db_name)

def sort_tests(data_list):
    out = {}
    for elem in data_list:
        try:
            out[elem[0]].extend(elem[1:])
        except KeyError:
            out[elem[0]] = list(elem)
    return [tuple(values) for values in out.values()]

def get_count_by_perc(data_list, max, min):
    count = 0
    for item in data_list:
        if item[0] <= max and item[0] >= min:
            count += 1
    return count

def main():
    args = parse_options()
    app.config['MYSQL_HOST'] = args.sqlhost
    app.config['MYSQL_USER'] = args.username
    app.config['MYSQL_PASSWORD'] = args.password
    app.config['auth_plugin'] = 'mysql_native_password'
    app.run(host=args.apphost, port=args.appport)