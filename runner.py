if True:                        # Command line options & Defaults
    import sys, os, argparse, shutil, itertools, time
    import datetime as dt
    import time
    from multiprocessing import Pool as _Pool
    _TIME_DURATION_UNITS = (('w', 60*60*24*7), ('d', 60*60*24),  ('h', 60*60), ('m', 60),  ('s', 1))
    _PROJECT_NAME = 'heuricar' # name of the project
    _WD = os.path.dirname(os.path.realpath(__file__)) # working directory (path of script)
    _PATH = _WD[0:(_WD.find(_PROJECT_NAME)+len(_PROJECT_NAME))]+'/' # path of the project
     
    _ARGS_IPYTHON = '-f test_script.py -w 2 -a '.split() # sys args for IPython (use if the script is run there)
    _ARGS_IPYTHON.append("-ctrn §1 -e 100 -do §2 -rc 100 -rn '<countrytrn>/<iterator>' -i 0")
    _ARGS_IPYTHON.append('-l')
    _ARGS_IPYTHON.append('UK+FR 0.5+0.4')
    if 'ipykernel' in sys.argv[0]:
        _args = _ARGS_IPYTHON
    else:
        _args = sys.argv[1:]
    os.chdir(_WD) # change to the directory of this file (just in case)

    _parser = _p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    _p.add_argument('-f', '--file', metavar='#', type=str, default='script.py',  help="script to run")
    _p.add_argument('-w', '--workers', metavar='#', type=int, default=1, help='number of workers')     
    _p.add_argument('-rf', '--resultsfolder', metavar='#', type=str, default='runs', help='results folder')
    _p.add_argument('-v', '--verbose', metavar='#', type=int, default=0, help='verbosity of each run')
    _p.add_argument('-a', '--args', metavar='#', type=str, default='',  help="agrs combination, e.g. '-e 5+10 -d 0.1+0.2'")
    _p.add_argument('-l', '--lists', metavar='#', type=str, default='',  help="corresponding lists e.g. '5+10 0.1+0.2'")
    _p.add_argument('-d', '--delay', metavar='#', type=int, default=5,  help="delay first runners by # seconds")
    conf = _parser.parse_args( _args)   # parse arguments

    def human_time(seconds):
        if seconds == 0:
            return '0s'
        parts = []
        for unit, div in _TIME_DURATION_UNITS:
            amount, seconds = divmod(int(seconds), div)
            if amount > 0:
                parts.append('{}{}'.format(amount, unit))
        return ' '.join(parts)


if True:                        # Prepare arguments
    s = conf.args
    s = s.split()
    runs = []
    for i in range(int(len(s)/2)):
        runs.append([s[i*2] + ' ' + e for e in s[i*2+1].split('+')])
    runs = [' '.join(p) for p in itertools.product(*runs)]

    if conf.lists != "":
        lists = conf.lists.split(' ')
        lists = [l.split('+') for l in lists]

        lists = list(map(list, zip(*lists))) #transpose

        runs2 = []
        for l in lists:
            for r in runs:
                r_tmp = r
                for i in range(len(l)):
                    r_tmp = r_tmp.replace("§"+str(i+1), l[i])
                runs2.append(r_tmp)
        runs = runs2

    n = len(runs)
    for i in range(n):
        runs[i] = [runs[i], i+1]




if True:                        # Backup file and logs
    os.makedirs(_PATH + conf.resultsfolder , exist_ok=True)
    shutil.copyfile(os.path.realpath(__file__) , _PATH + conf.resultsfolder + '/'  + os.path.basename(__file__)  )
    _cmd = 'python3 ' + os.path.basename(__file__) + ' ' + ' '.join(_args[:-1]) + " '" + _args[-1] + "'"
    with open(_PATH + conf.resultsfolder + "/runner_args.txt","a") as file:
        file.write(_cmd+'\n')
    _logpath = _PATH + conf.resultsfolder + "/runner_log.txt"


if True:                        # Worker
    _t_total= time.time()
    def proc(run):     # Called by each worker  
        _r_time = time.time()
        if conf.delay:
            if run[1] <= conf.workers:
                time.sleep(conf.delay*(run[1]-1))
        os.system('python3 ' + conf.file + ' -sa 1 -rf ' + conf.resultsfolder + ' ' + run[0] + (' > /dev/null' if not conf.verbose else '') )
        _elapsed = time.time() - _r_time
        s = str(dt.datetime.now())[:19] + ' Completed: ' + str(run[1]) + " / " + str(n) + ' in ' + human_time(_elapsed) + ' ETA: ' + human_time(_elapsed * ((n - run[1])  / conf.workers))
        with open(_logpath,"a") as logfile:
            logfile.write(s + '\n')
        print(s)


if __name__ == '__main__':      # Main program
    pool = _Pool(processes=conf.workers)
    pool.imap(proc, runs)
    pool.close()
    pool.join()
    s = str(dt.datetime.now())[:19] + ' All finished! This took: ' + human_time(time.time() - _t_total)
    with open(_logpath,"a") as logfile:
        logfile.write(s + '\n')
    print(s)
