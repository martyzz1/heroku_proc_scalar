from setuptools import setup, find_packages

setup(
    name='heroku_proc_scalar',
    version='2.0.3',
    description="A suite of tools (mainly for Celery/Redis|IronMQ Backend) designed to allow safe shuting down of heroku procs that need to ibe terminated gracefull with SIGTERM - that likely take longer than heroku's 10 second rule. use in conjunction with the heroku_proc_scala_app",
    author='Martin Moss',
    author_email='martin_moss@btinternet.com',
    url='http://github.com/martyzz1/heroku_proc_scalar',
    license='MIT',
    packages=find_packages(),
    keywords='celery, djcelery, heroku, autoscaling, redis, iron_mq',
    zip_safe=True,
    install_requires=[
        'Fabric==1.4.3',
        'celery>=3.1.0',
        'heroku-dev>=3.0.1',
        'redis==2.7.5',
    ],
    dependency_links=[
        'https://github.com/martyzz1/heroku.py/zipball/dc95800c0dbfc52d37f77d504af25bf190264eff#egg=heroku-dev-3.0.0'
    ]
)
