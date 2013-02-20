Import('env')
src = ['echidna.c']
libs = ['usb-1.0','mcdaq','getoptpp','zmq','m','fftw3']
libs.reverse()

libpaths=['/usr/local/lib',
          '#lib/mcdaq',
          '#lib/siggen',
          '#lib/getoptpp']

libs_cv = ['opencv_core','opencv_imgproc',
           'opencv_highgui','opencv_ml',
           'opencv_video','opencv_features2d',
           'opencv_calib3d','opencv_objdetect',
           'opencv_contrib','opencv_legacy',
           'opencv_flann']

libs = libs + libs_cv

libs_audio = ['portaudio']

libs = libs + libs_audio


Clean('.','build/')

env.VariantDir('build/', 'src/')
env.Program(target='echidna',CCFLAGS='-g',
        LIBPATH=libpaths,LIBS=libs,source=src)

src = ['echidna2.cpp']

flags = { "CPPPATH": ['/usr/local/include/eigen3',
                      '/usr/include/eigen3',
                      '/usr/include',
                      '#lib/siggen',
                      '#lib/getoptpp']}
env.MergeFlags(flags)
env.ParseConfig("pkg-config --cflags opencv")
env.ParseConfig("pkg-config --libs opencv")

env.Program(target='echidna2',CCFLAGS='-g',
        LIBPATH=libpaths,LIBS=libs,source=src)

src = ['echidna_server.cpp']
env.Program(target='echidna_server',CCFLAGS='-g',
        LIBPATH=libpaths,LIBS=libs,source=src)

src = ['echidna_client.cpp']
env.Program(target='echidna_client',CCFLAGS='-g',
        LIBPATH=libpaths,LIBS=libs,source=src)
