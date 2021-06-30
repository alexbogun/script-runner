Simple runner-sript to schedule multiple runs of the worker-script with different arguments and in parallel.

-f: the name of the script to execute
-w: defines number of parallel workers to use
-d: sets delay before starting next worker
-of: parent folder to store set of runs
-rf: folder to store current set of runs
-a: (followed by string in "") contains arguments passed to individual scripts:
	"+" will result in individual runs containing each parameter e.g. "1+2" will run script twice with "1" and "2"
        "#" will create ranges, e.g. "#5" will be replaced with "1+2+3+4+5" and "#5:7" with "5+6+7"
	"§" will replace values from lists (see below)

-l: (followed by string in "") contains lists to replace "§" with:
	e.g. -l "NN+CB #5+1" will replace §1, §2 with ("NN", "#5") and ("CB", "1") respectively


Example usage:
runner.py -w 2 -f script.py -a "-e 100+150 -do 0.1+0.5" 

The above will run script.py 4 times with following parameters:
"-e 100 -do 0.1"
"-e 150 -do 0.1"
"-e 100 -do 0.5"
"-e 150 -do 0.5"

It will also be executed in parallel with 2 concurent workers.

 
Usage example2: 
runner.py -w 2 -f script.py -a "-m -es 0+1 §1 -i §2" -l "NN+CB #5+1"

this will run 22 models: 10 NN models each with es=0 & es=1, and 1 CB models each with es=0 & es=1
