import zipfile
import os
import shutil

APP_XML = 'app.xml'
JAR_FILE = 'target/wisesdn-1.0-SNAPSHOT.jar'
OAR_FILE = 'target/wisesdn-1.0-SNAPSHOT.oar'
M2_PATH = 'm2/org/onosproject/wisesdn/1.0-SNAPSHOT/wisesdn-1.0-SNAPSHOT.jar'

if not os.path.exists(JAR_FILE):
    print(f"Error: {JAR_FILE} not found!")
    exit(1)

print(f"Creating {OAR_FILE}...")
with zipfile.ZipFile(OAR_FILE, 'w') as zf:
    zf.write(APP_XML, 'app.xml')
    zf.write(JAR_FILE, M2_PATH)

print("Done.")
