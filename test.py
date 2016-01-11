from sqlstatement import *

stmnt = 'CREATE TABLE table (yogoy TYPE constraint, CONStraint hello);'
print('level 2')
c = Create(2)
c.UploadStatement(stmnt)
c.DownloadStatement()
print('level 1')
c1 = Create(1)
c1.UploadStatement(stmnt)
print('level 0')
c2 = Create()
c2.UploadStatement(stmnt)
