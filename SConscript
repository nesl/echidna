Import('env')
src = ['echidna.c']
libs = ['usb-1.0','mcdaq']
libs.reverse()

libpaths=['/usr/local/lib','#lib/mcdaq']
Clean('.','build/')
env.VariantDir('build/', 'src/')
env.Program(target='echidna',CCFLAGS='-g',
        LIBPATH=libpaths,LIBS=libs,source=src)

