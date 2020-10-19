Simple runner-sript to schedule multiple runs of the worker-script with different arguments and in parallel.

Example usage:
runner.py -w 2 -f script.py -a "-e 100+150 -do 0.1+0.5" 

The above will run script.py 4 times with following parameters:
"-e 100 -do 0.1"
"-e 150 -do 0.1"
"-e 100 -do 0.5"
"-e 150 -do 0.5"

It will also be executed in parallel with 2 concurent workers.