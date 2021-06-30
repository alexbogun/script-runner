#!/usr/bin/env python3
# %% 
if True:                        # Imports, command line options & defaults
    import sys, os, argparse, shutil, itertools, time
    import datetime as dt
    import time
    import pytz
    import yaml
    import re
    from multiprocessing import Pool as _Pool

    _CONF_FILE ='runner_config.yaml'                               # name of config file for this runner
    _ARGS_FILE ='runner_args.txt'                                   # file to store arguments
    _LOG_FILE = 'runner_log.txt'                                    # file to save logs
    _TIMEZONE = 'Europe/Amsterdam'                                  # Time zone to use
    _PROJDIR = os.getcwd() + '/'                                    # project directory

    # sys args for Jupyter. Use to supply arguments if the script is run there)
    _ARGS_IPYTHON = ''.split() 

    if 'ipykernel' in sys.argv[0]: 
        _args = _ARGS_IPYTHON       # this enables running in Jupyter Notebook
    else:
        _args = sys.argv[1:]        # regular use in console

    _parser = _p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, 
    description='Script runner / scheduler. \nUsage example: runner.py -w 2 -f mnist.py -a "-m -es 0+1 §1 -i §2" -l "NN+CB #5+1" ' + 
    '\n-> this will run 22 models: 10 NN models each with es=0 & es=1, and 1 CB models each with es=0 & es=1' +  '\n' +
    '\nExplanation: -a "" contains arguments passed to individual scripts; values separated by "+" will' + 
    '\n             be combined in individual runs;' +
    '\n             -l "NN+CB #5+1" will replace §1, §2 with "NN", "#5" and "CB", "1" respectively'+
    '\n             #5 will be replaced with 1+2+3+4+5, #5:7 with 5+6+7')
    _p.add_argument('-f', '--file', metavar='#', type=str, default='mnist.py',  help="script to run")
    _p.add_argument('-w', '--workers', metavar='#', type=int, default=4, help='number of workers')     
    _p.add_argument('-of', '--outfolder', metavar='#', type=str, default='zoos', help='output folder')
    _p.add_argument('-rf', '--runfolder', metavar='#', type=str, default='mnist', help='run folder')
    _p.add_argument('-v', '--verbose', metavar='#', type=int, default=0, help='verbosity of each run')
    _p.add_argument('-a', '--arguments', metavar='#', type=str, default='-sa 1 -i §1 -rn model_iterator',  help="agrs combination, e.g. '-e 5+10 -d 0.1+0.2'")
    _p.add_argument('-l', '--lists',    metavar='#', type=str, default='#10',  help="corresponding lists e.g. 'NN+CB 0.1+0.2'")
    _p.add_argument('-d', '--delay', metavar='#', type=int, default=1,  help="delay first runners by # seconds")
    _p.add_argument('-cf', '--config', metavar='#', type=str, default='', help='path to config file, "no": do not use')
    conf = _parser.parse_args( _args)   # parse arguments

    if (conf.config == '') or (conf.config == 'no'):        # no reading config file
        conf.args = ' '.join(_args)
    else:                                       #  reading config file
        conf.config = conf.config + ".yaml"
        with open(conf.config) as file:
            _config = yaml.load(file) 
        conf = _parser.parse_args( _args, _config)  
        if not hasattr(conf,'args'):
            conf.args = ''
        conf.args = conf.args + ' '.join(_args)

    _EXPDIR = _PROJDIR + conf.outfolder + '/' + conf.runfolder


if True:                        # Functions
    _TIME_DURATION_UNITS = (('w', 60*60*24*7), ('d', 60*60*24),  ('h', 60*60), ('m', 60),  ('s', 1))

    def human_time(seconds):    # function to convert time to human readable format
        if seconds == 0:
            return '0s'
        parts = []
        for unit, div in _TIME_DURATION_UNITS:
            amount, seconds = divmod(int(seconds), div)
            if amount > 0:
                parts.append('{}{}'.format(amount, unit))
        return ' '.join(parts)


if True:                        # Prepare arguments
    s = conf.arguments   # arguments passed to runner script
    s = s.split()  
    runs = []       # List of parameters for separate runs
    for i in range(int(len(s)/2)):  # break into argument groups
        runs.append([s[i*2] + ' ' + e for e in s[i*2+1].split('+')])
    runs = [' '.join(p) for p in itertools.product(*runs)]  # intersect argument groups to create all possible combinations

    if (conf.lists != ""):  # Fill in lists 
        lists = conf.lists.split(' ')
        lists = [l.split('+') for l in lists]
        lists = list(map(list, zip(*lists))) #transpose
        runs2 = []
        for l in lists:
            for r in runs:
                r_tmp = r
                for i in range(len(l)):
                    r_tmp = r_tmp.replace("§"+str(i+1), l[i]) # replace §1 with first element of list §2 with second, etc.
                runs2.append(r_tmp)
        runs = runs2
    
    runs3=[]        # process iterators #3 = 1+2+3
    for r in runs:
        if r.find('#')>=0:
            s1 = re.search(r'#\S+', r)[0]
            if s1.find(':')>=0:
                num1, num2 = [int(i) for i in s1[1:].split(':')]
            else:
                num1, num2 = 1, int(s1[1:])
            for i in range(num1, num2+1):
                runs3.append( r.replace(s1, str(i)) )
        else:
            runs3.append(r) 
    runs = runs3
    
    n = len(runs)       # add run numbers to list
    for i in range(n):
        runs[i] = [runs[i], i+1]


if True:                        # Backup file and logs
    os.makedirs(_EXPDIR, exist_ok=True)
    shutil.copyfile(os.path.realpath(__file__) , _EXPDIR  + '/'  + os.path.basename(__file__)  )
    with open(_EXPDIR  + '/' + _CONF_FILE, 'w') as file:
        yaml.dump(conf, file)
    _cmd = 'python3 ' + os.path.basename(__file__) + ' '.join(_args)
    with open(_EXPDIR + "/" + _ARGS_FILE,"a") as file:
        file.write(_cmd+'\n')
    _logpath = _EXPDIR + "/" + _LOG_FILE


if True:                        # Worker
    _t_total= time.time()
    def proc(run):     # Called by each worker  
        _r_time = time.time()
        if conf.delay:
            if run[1] <= conf.workers:
                time.sleep(conf.delay*(run[1]-1))
        os.system('python3 ' + conf.file + ' ' + run[0] + (' > /dev/null' if not conf.verbose else '') )
        _elapsed = time.time() - _r_time
        s = str(dt.datetime.now(tz=pytz.timezone(_TIMEZONE)))[:19] + ' Completed: ' + str(run[1]) + " / " + str(n) + ' in ' + human_time(_elapsed) + ' ETA: ' + human_time(_elapsed * ((n - run[1])  / conf.workers))
        with open(_logpath,"a") as logfile:
            logfile.write(s + '\n')
        print(s)


if __name__ == '__main__':      # Main program
    pool = _Pool(processes=conf.workers)
    pool.imap(proc, runs)
    pool.close()
    pool.join()
    s = str(dt.datetime.now(tz=pytz.timezone(_TIMEZONE)))[:19] + ' All finished! This took: ' + human_time(time.time() - _t_total)
    with open(_logpath,"a") as logfile:
        logfile.write(s + '\n')
    print(s)

