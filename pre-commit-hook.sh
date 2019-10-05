#!/bin/sh

echo 'Running tests'

git stash > /dev/null
python -m unittest discover -s test/ -p '*_test.py'
if [[ $? -ne 0 ]]; then
	echo 'Aborting commit (Attempting to commit a repository where the test suite fails)'
	echo 'Bypass with git commit --no-verify'
	git stash pop > /dev/null
	exit 1
fi 
git stash pop > /dev/null

exit 0
