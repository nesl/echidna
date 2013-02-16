# Build Script for Data dump from USB-1608FS
import os

env = Environment()
    


subdirs = ['lib/mcdaq','lib/getoptpp']
for dir in subdirs:
        print os.path.join(dir, 'SConscript')
        SConscript( os.path.join(dir, 'SConscript'), exports = ['env'])

build_dir = 'build/'
Clean('.',build_dir)
Clean('.','testfile.csv')
SConscript('SConscript', variant_dir='build', duplicate=0, exports = ['env', 'build_dir'])

