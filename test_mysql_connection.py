import MySQLdb

try:
    conn = MySQLdb.connect(
        host='localhost',
        user='xcsm_admin',
        passwd='xcsm.4gi.enspy27',
        db='xcsm_db'
    )
    print("✅ Connexion MySQL réussie avec xcsm_admin")
    
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"   Version MySQL: {version[0]}")
    
    cursor.execute("SHOW DATABASES LIKE 'xcsm_db'")
    db_exists = cursor.fetchone()
    if db_exists:
        print("✅ Base xcsm_db existe")
    else:
        print("❌ Base xcsm_db n'existe pas")
    
    conn.close()
    
except MySQLdb.Error as e:
    print(f"❌ Erreur MySQL: {e}")
    print("\nVérifiez dans PHPMyAdmin:")
    print("1. La base 'xcsm_db' existe-t-elle?")
    print("2. L'utilisateur 'xcsm_admin'@'localhost' existe-t-il?")
    print("3. Les privilèges sont-ils accordés?")
