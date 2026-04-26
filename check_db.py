import psycopg2

conn = psycopg2.connect(
    database='mit_recordkeeping_db',
    user='postgres',
    password='011304',
    host='localhost',
    port='5432'
)
cursor = conn.cursor()

print('=== Users named Marwina ===')
cursor.execute(
    "SELECT id, username, email, first_name, last_name FROM auth_user WHERE first_name LIKE '%Marwina%'")
for row in cursor.fetchall():
    print(f'User ID: {row[0]}, Email: {row[2]}, Name: {row[3]} {row[4]}')

print('\n=== All Applications ===')
cursor.execute('''SELECT a.id, a.application_id, a.user_id, a.status, u.email 
                  FROM admin_app_application a 
                  JOIN auth_user u ON a.user_id = u.id''')
for row in cursor.fetchall():
    print(
        f'App ID: {row[1]}, User ID: {row[2]}, Status: {row[3]}, Email: {row[4]}')

print('\n=== DocumentVerification Statuses ===')
cursor.execute('''SELECT dv.id, dv.status, d.document_type, d.user_id, u.email 
                  FROM admin_app_documentverification dv 
                  JOIN students_app_document d ON dv.document_id = d.id
                  JOIN auth_user u ON d.user_id = u.id
                  ORDER BY u.email, d.document_type''')
print(f"{'Status':<15} | {'Document Type':<30} | Email")
print("-" * 60)
for row in cursor.fetchall():
    status = row[1] if row[1] else 'None'
    doc_type = row[2] if row[2] else 'Unknown'
    email = row[4] if row[4] else 'Unknown'
    print(f"{status:<15} | {doc_type:<30} | {email}")

cursor.close()
conn.close()
