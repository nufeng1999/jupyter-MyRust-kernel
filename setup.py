from setuptools import setup

setup(name='jupyter_MyRust_kernel',
      version='0.0.1',
      description='Minimalistic Rust kernel for Jupyter',
      author='nufeng',
      author_email='18478162@qq.com',
      license='MIT',
      classifiers=[
          'License :: OSI Approved :: MIT License',
      ],
      url='https://github.com/nufeng1999/jupyter-MyRust-kernel/',
      download_url='https://github.com/nufeng1999/jupyter-MyRust-kernel/tarball/0.0.1',
      packages=['jupyter_MyRust_kernel'],
      scripts=['jupyter_MyRust_kernel/install_MyRust_kernel'],
      keywords=['jupyter', 'notebook', 'kernel', 'rust','rs'],
      include_package_data=True
      )
