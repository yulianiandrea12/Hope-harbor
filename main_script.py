import subprocess
import psutil
import os

def is_running(script):
    for q in psutil.process_iter():
        if q.name().startswith('python'):
            if len(q.cmdline())>1 and script in q.cmdline()[1] and q.pid !=os.getpid():
                # print("'{}' Process is already running".format(script))
                return True

    return False


if not is_running("/home/Projects/visualiti-py/manage.py"):
    print ("NOT RUN")
    subprocess.call('source /home/Projects/visualiti-py/prod/bin/activate', shell=True)
    subprocess.check_call(["/home/Projects/visualiti-py/prod/bin/python", "/home/Projects/visualiti-py/manage.py", "runserver", "localhost:55555"])