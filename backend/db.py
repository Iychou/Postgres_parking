import oracledb

connection = oracledb.connect(

user="erp",

password="erp123",

dsn="192.168.226.137:1521/ORCLCDB"

)

def get_connection():

    return connection