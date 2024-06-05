@echo off

set id="tt3743822"
set customid="Fear the Walking Dead"
set seasoncount=8

for /l %%x in (1, 1, %seasoncount%) do (
	python tvrip.py -src "Vidplay" -id %id% -se %%x -ep 1 -endep 30 -cid %customid%
)