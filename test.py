


def main():
	print('test')



if __name__ == '__main__':
    main()



import rds_config
import pymysql
import sys

rds_host  = db_endpoint
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)



def test_db_con():
    with conn.cursor() as cur:
        cur.execute("create table Employee3 ( EmpID  int NOT NULL, Name varchar(255) NOT NULL, PRIMARY KEY (EmpID))")  
        cur.execute('insert into Employee3 (EmpID, Name) values(1, "Joe")')
        cur.execute('insert into Employee3 (EmpID, Name) values(2, "Bob")')
        cur.execute('insert into Employee3 (EmpID, Name) values(3, "Mary")')
        conn.commit()
        cur.execute("select * from Employee3")
        for row in cur:
            item_count += 1
            logger.info(row)
            #print(row)
    conn.commit()
    
    return Added %d items from RDS MySQL table" %(item_count)